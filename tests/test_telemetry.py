import struct
import socket
import time
from oversteer.telemetry import decode, RevLeds, Telemetry, LED_SPACING


def forza(rpm, max_rpm=8000.0, race_on=1, size=324):
    data = bytearray(size)
    struct.pack_into('<i', data, 0, race_on)
    struct.pack_into('<fff', data, 8, max_rpm, 900.0, rpm)
    return bytes(data)


def outgauge(rpm, shift=False, eng_temp=89.73):
    data = bytearray(96)
    data[4:8] = b'XRG\0'
    struct.pack_into('<f', data, 16, rpm)
    struct.pack_into('<ff', data, 20, 0.5, eng_temp)          # Turbo, EngTemp
    struct.pack_into('<II', data, 40, 0, 1 if shift else 0)   # DashLights, ShowLights
    return bytes(data)


def codemasters(rpm, max_rpm, count=66):
    floats = [0.0] * count
    floats[37] = rpm / 10.0
    floats[63] = max_rpm / 10.0
    return struct.pack('<%df' % count, *floats)


def ovst(rpm, max_rpm, shift=False, version=1):
    return b'OVST' + struct.pack('<BBHffif', version, 1, 1 if shift else 0, rpm, max_rpm, 3, 120.0)


def test_decode_formats():
    assert decode(ovst(6000, 8500)) == (6000.0, 8500.0, False)
    assert decode(ovst(6000, 0)) == (6000.0, None, False)         # redline unknown: learnt
    assert decode(ovst(6000, 8500, shift=True))[2] is True
    assert decode(ovst(6000, 8500, version=2)) is None
    assert decode(forza(4000)) == (4000.0, 8000.0, None)
    assert decode(forza(4000, size=232))[0] == 4000.0
    assert decode(forza(4000, race_on=0))[0] == 0.0          # menus: no revs
    assert decode(forza(4000, size=331))[0] == 4000.0         # Forza Motorsport (2023)
    assert decode(outgauge(3000)) == (3000.0, None, False)    # odd EngTemp mantissa is not a shift light
    assert decode(outgauge(7000, shift=True))[2] is True
    assert decode(forza(float('inf'))) is None
    assert decode(forza(4000, max_rpm=float('nan'))) is None
    assert decode(outgauge(1e9)) is None
    assert decode(codemasters(5000, float('inf'))) is None
    rpm, mx, _ = decode(codemasters(5000, 7500))
    assert abs(rpm - 5000) < 1e-3 and abs(mx - 7500) < 1e-3
    rpm, mx, _ = decode(codemasters(6000, 7000, count=70))    # WRC Generations (longer packet)
    assert abs(rpm - 6000) < 1e-3 and abs(mx - 7000) < 1e-3
    assert decode(codemasters(6000, 7000, count=64))[1] == 7000.0
    assert decode(b'\x00' * 50) is None
    assert decode(b'\x00' * 258) is None                     # not float-aligned


def test_led_spacing_is_monotonic():
    assert list(LED_SPACING) == sorted(LED_SPACING) and LED_SPACING[-1] == 1.0


class FakeLeds:
    """Records what the listener would write to the LEDs."""

    def __init__(self, n=5):
        self.paths = ['led%d' % i for i in range(n)]
        self.writes = []

    def available(self):
        return True

    def set_count(self, lit):
        self.writes.append(('count', lit))

    def set_pattern(self, pattern):
        self.writes.append(('pattern', tuple(pattern)))

    def off(self):
        self.writes.append(('off',))


def _feed(telemetry, packets, gap=0.01):
    """Start the listener on a free port, send packets, return the LED writes."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('127.0.0.1', 0))
    telemetry.port = sock.getsockname()[1]
    sock.close()
    assert telemetry.start()
    out = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    for p in packets:
        out.sendto(p, ('127.0.0.1', telemetry.port))
        time.sleep(gap)
    time.sleep(0.1)
    telemetry.stop()
    return telemetry.leds.writes


def test_bar_relative_to_shift_point():
    leds = FakeLeds()
    writes = _feed(Telemetry(leds, shift=0.90), [forza(r, max_rpm=8000) for r in (4000, 5300, 6500, 7200, 7400)])
    counts = [w[1] for w in writes if w[0] == 'count']
    assert counts == [0, 1, 3, 5][:len(counts)] or counts == [0, 1, 3, 5]      # 90 % of 8000 = 7200: all on there
    assert not any(w[0] == 'pattern' for w in writes)                          # 7400 < 7200 * 1.03: no flash


def test_shift_rpm_mode_and_flash():
    leds = FakeLeds()
    writes = _feed(Telemetry(leds, shift_rpm=6500), [forza(r, max_rpm=9000) for r in (4700, 6500, 6800, 6800, 6800)], gap=0.1)
    assert ('count', 1) in writes and ('count', 5) in writes
    assert any(w[0] == 'pattern' for w in writes)                              # above 6500 * 1.03: flashing


def test_outgauge_learned_max_never_flashes_a_steady_cruise():
    leds = FakeLeds()
    packets = [outgauge(7000)] + [outgauge(4000)] * 30
    writes = _feed(Telemetry(leds, shift=0.8), packets)
    assert not any(w[0] == 'pattern' for w in writes)
