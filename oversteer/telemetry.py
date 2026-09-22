"""Game telemetry -> wheel rev LEDs.

A small UDP listener understands the telemetry formats that cross the
Proton boundary and turns engine RPM into the wheel's five rev LEDs:

- Forza Horizon / Motorsport "Data Out" (sled 232 bytes, FM7 dash 311,
  FH4+ dash 324, FM 2023 dash 331): EngineMaxRpm at 8, EngineIdleRpm at 12,
  CurrentEngineRpm at 16 as little-endian floats, IsRaceOn at 0. Enable it
  in the game under Settings > HUD and gameplay > Data Out, pointing at this
  machine's IP and the port set here.
- OutGauge (BeamNG.drive, Live for Speed): 92/96 bytes, rpm as a float at
  16, the shift-light flag (DL_SHIFT) in the ShowLights word at 44. There is
  no max RPM in the packet, so the ceiling is learnt from the highest RPM
  seen and forgotten when the telemetry stops.
- Codemasters extradata=3 (DiRT Rally 2.0, DiRT 4) and the games that copy
  its layout (WRC 10 / WRC Generations native telemetry): 64 or more
  little-endian floats, engine rate at index 37 and max at 63, both in
  rpm / 10. The packet length varies by game, so any 4-byte-aligned length
  from 256 bytes up is accepted once the Forza sizes are excluded.

- Oversteer's own "OVST" datagram (24 bytes) from oversteer-shm-bridge, the
  helper that runs inside a Proton prefix and forwards shared-memory
  telemetry (Assetto Corsa, Assetto Corsa Competizione, Assetto Corsa
  Rally): rpm, max rpm (0 = unknown), gear, speed.

The listener runs in a daemon thread and writes the LED brightness files
through :class:`RevLeds`; when no packet arrives for a while the LEDs go
out so a stale value never stays lit.
"""

import glob
import logging
import math
import os
import socket
import struct
import threading
import time

DEFAULT_PORT = 5300
DEFAULT_SHIFT = 0.97                                 # shift point as a fraction of max RPM
LED_SPACING = (0.72, 0.80, 0.89, 0.95, 1.0)          # per LED, as a fraction of the shift point
FLASH_MARGIN = 0.03                                  # above the shift point: flash (shift now)
LEARNED_DECAY = 0.01                                 # OutGauge: learnt ceiling sags this much per second
IDLE_TIMEOUT = 2.0                                   # seconds without telemetry -> LEDs off
FLASH_PERIOD = 0.08                                  # limiter flash half-period (seconds)
RPM_LIMIT = 30000.0                                  # anything above is not an engine speed
FORZA_SIZES = (232, 311, 324, 331)
CODEMASTERS_MIN = 64 * 4                             # DR2/DiRT 4 extradata 3 is 264, WRCG is longer
CODEMASTERS_MAX = 512
OVST_MAGIC = b'OVST'
OVST_SIZE = 24


class RevLeds:
    """The wheel's rev LEDs (Linux LED class), lit as a bar."""

    def __init__(self, sysfs_device_path):
        pattern = os.path.join(sysfs_device_path, 'leds', '*RPM*', 'brightness')
        self.paths = sorted(glob.glob(pattern), key=lambda p: os.path.dirname(p))
        self._last = None

    def available(self):
        return bool(self.paths) and all(os.access(p, os.W_OK) for p in self.paths)

    def set_count(self, lit):
        """Light the first `lit` LEDs."""
        pattern = tuple(i < lit for i in range(len(self.paths)))
        self.set_pattern(pattern)

    def set_pattern(self, pattern):
        pattern = tuple(bool(x) for x in pattern)
        if pattern == self._last:
            return
        for path, on in zip(self.paths, pattern):
            try:
                with open(path, 'w') as f:
                    f.write('1' if on else '0')
            except OSError as e:
                logging.debug("led %s: %s", path, e)
        self._last = pattern

    def off(self):
        self.set_pattern((False,) * len(self.paths))

    def test(self, step=0.15):
        """Light the LEDs in sequence, then all, then off (blocking)."""
        n = len(self.paths)
        for i in range(n + 1):
            self.set_count(i)
            time.sleep(step)
        for _ in range(3):
            self.set_pattern((True,) * n)
            time.sleep(step)
            self.off()
            time.sleep(step)


def _plausible(x):
    return math.isfinite(x) and -RPM_LIMIT < x < RPM_LIMIT


def decode(data):
    """Return (rpm, max_rpm or None, shift_light or None) or None if the
    packet isn't a telemetry format we know (or carries nonsense)."""
    n = len(data)
    if n == OVST_SIZE and data[:4] == OVST_MAGIC:
        version, source, flags, rpm, max_rpm, gear, speed = struct.unpack_from('<BBHffif', data, 4)
        if version != 1 or not (_plausible(rpm) and _plausible(max_rpm)):
            return None
        return (max(0.0, rpm), max_rpm if max_rpm > 0 else None, bool(flags & 1))
    if n in FORZA_SIZES:
        race_on = struct.unpack_from('<i', data, 0)[0]
        max_rpm, idle_rpm, rpm = struct.unpack_from('<fff', data, 8)
        if not (_plausible(max_rpm) and _plausible(rpm)):
            return None
        if race_on == 0 or max_rpm <= 0:
            return (0.0, max_rpm if max_rpm > 0 else None, None)
        return (max(0.0, rpm), max_rpm, None)
    if n in (92, 96):
        car = data[4:8]
        if any(b and not 0x20 <= b < 0x7f for b in car):     # Car[4]: short ASCII name
            return None
        rpm = struct.unpack_from('<f', data, 16)[0]
        if not _plausible(rpm):
            return None
        dashlights, showlights = struct.unpack_from('<II', data, 40)
        shift = bool(showlights & (1 << 0))          # DL_SHIFT
        return (max(0.0, rpm), None, shift)
    if CODEMASTERS_MIN <= n <= CODEMASTERS_MAX and n % 4 == 0:
        floats = struct.unpack_from('<64f', data, 0)
        rpm, max_rpm = floats[37] * 10.0, floats[63] * 10.0
        if not (_plausible(max_rpm) and _plausible(rpm)) or max_rpm <= 0:
            return None
        return (max(0.0, rpm), max_rpm, None)
    return None


class Telemetry:
    """UDP listener thread driving a RevLeds."""

    def __init__(self, leds, port=DEFAULT_PORT, shift=DEFAULT_SHIFT, shift_rpm=None, on_status=None):
        """`shift` is the shift point as a fraction of the game's max RPM;
        `shift_rpm`, when given, is an absolute shift point instead."""
        self.leds = leds
        self.port = int(port)
        self.set_shift(shift, shift_rpm)
        self.last_max_rpm = 0.0
        self._learned_at = 0.0
        self.on_status = on_status
        self.running = False
        self.last_packet = 0.0
        self.last_source = None
        self.learned_max = 0.0
        self._thread = None
        self._sock = None
        self._unknown_sizes = set()

    def set_shift(self, shift=DEFAULT_SHIFT, shift_rpm=None):
        """Change the shift point while running (plain attribute writes:
        the listener thread reads them once per packet)."""
        self.shift = max(0.5, min(1.0, float(shift)))
        self.shift_rpm = float(shift_rpm) if shift_rpm else None

    def start(self):
        if self._thread is not None:
            return True
        try:
            # No SO_REUSEADDR: UDP has no TIME_WAIT, and with it a second
            # listener would silently share the port instead of failing.
            self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self._sock.bind(('0.0.0.0', self.port))
            self._sock.settimeout(0.25)
        except OSError as e:
            logging.warning("telemetry: cannot listen on UDP %d: %s", self.port, e)
            self._sock = None
            return False
        self.running = True
        self._thread = threading.Thread(target=self._run, name='telemetry', daemon=True)
        self._thread.start()
        return True

    def stop(self):
        self.running = False
        if self._thread is not None:
            self._thread.join(1.0)
            self._thread = None
        if self._sock is not None:
            self._sock.close()
            self._sock = None
        self.leds.off()

    def _run(self):
        lit_state = None            # LEDs lit as a bar; None = unknown, rewrite on next packet
        flash = False
        flash_at = 0.0
        while self.running:
            try:
                data, addr = self._sock.recvfrom(2048)
            except socket.timeout:
                if self.last_packet and time.monotonic() - self.last_packet > IDLE_TIMEOUT:
                    self.leds.off()
                    lit_state = None
                    self.last_packet = 0.0
                    self.last_source = None
                    self.learned_max = 0.0
                    self._learned_at = 0.0
                    self._status(None)
                continue
            except OSError:
                break
            decoded = decode(data)
            if decoded is None:
                if len(data) not in self._unknown_sizes:
                    self._unknown_sizes.add(len(data))
                    logging.info("telemetry: unknown %d-byte packet from %s", len(data), addr[0])
                continue
            rpm, max_rpm, shift = decoded
            now = time.monotonic()
            self.last_packet = now
            if self.last_source != addr[0]:
                self.last_source = addr[0]
                self._status(addr[0])
            shift_rpm, shift_fraction = self.shift_rpm, self.shift
            if max_rpm is None:
                # OutGauge: learn the ceiling from the highest RPM seen. It
                # sags slowly (per second, not per packet) so a change of
                # car with a lower redline still fills the bar, but never
                # below what keeps the current RPM at "all on": a steady
                # cruise must not turn into a limiter flash (OutGauge has
                # its own shift-light flag for that).
                if self._learned_at:
                    self.learned_max *= max(0.0, 1.0 - LEARNED_DECAY * (now - self._learned_at))
                self._learned_at = now
                self.learned_max = max(self.learned_max, rpm, rpm / shift_fraction if not shift_rpm else 0.0)
                max_rpm = self.learned_max
            else:
                self.last_max_rpm = max_rpm
            # Everything is relative to the shift point: the bar completes
            # there and flashes above it.
            reference = shift_rpm if shift_rpm else shift_fraction * max_rpm
            fraction = rpm / reference if reference > 0 else 0.0
            if shift or fraction >= 1.0 + FLASH_MARGIN:
                if now - flash_at >= FLASH_PERIOD:
                    flash = not flash
                    flash_at = now
                    self.leds.set_pattern((flash,) * len(self.leds.paths))
                lit_state = None
                continue
            lit = sum(1 for t in LED_SPACING if fraction >= t)
            if lit != lit_state:
                self.leds.set_count(lit)
                lit_state = lit

    def _status(self, source):
        if self.on_status is not None:
            try:
                self.on_status(source)
            except Exception:
                pass
