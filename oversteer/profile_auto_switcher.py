import configparser
import logging
import os
import subprocess
import threading
import time

from .process_watcher import get_running_processes, detect_game

logger = logging.getLogger(__name__)

SETTINGS_KEYS = [
    ("range", "Range"),
    ("ff_gain", "FF Gain"),
    ("autocenter", "Autocenter"),
    ("spring_level", "Spring"),
    ("damper_level", "Damper"),
    ("friction_level", "Friction"),
    ("combine_pedals", "Combine Pedals"),
    ("ffb_leds", "FFB LEDs"),
]


def _format_settings(data):
    parts = []
    for key, label in SETTINGS_KEYS:
        val = data.get(key)
        if val is not None:
            parts.append(f"{label}: {val}")
    return ", ".join(parts)


def send_notification(title, message):
    """Send a desktop notification via notify-send."""
    try:
        subprocess.Popen(
            ["notify-send", "-a", "Oversteer", "-i", "input-gaming", title, message],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except FileNotFoundError:
        logger.debug("notify-send not found, skipping notification")


def load_profile_processes(profile_path):
    """
    Scan all profile INI files and return a dict:
    {profile_name: [process_name, ...]}
    Only profiles with a 'game_processes' key are included.
    """
    result = {}
    if not os.path.isdir(profile_path):
        return result
    for filename in os.listdir(profile_path):
        if not filename.endswith(".ini"):
            continue
        profile_name = filename[:-4]
        filepath = os.path.join(profile_path, filename)
        config = configparser.ConfigParser()
        config.read(filepath)
        if "profile" in config and "game_processes" in config["profile"]:
            raw = config["profile"]["game_processes"]
            procs = [p.strip() for p in raw.split(",") if p.strip()]
            if procs:
                result[profile_name] = procs
    return result


class ProfileAutoSwitcher:
    """Background thread that watches for game processes and auto-switches profiles."""

    def __init__(
        self,
        model,
        profile_path,
        poll_interval=2.0,
        on_profile_change=None,
        headless=False,
    ):
        self.model = model
        self.profile_path = profile_path
        self.poll_interval = poll_interval
        self.on_profile_change = on_profile_change
        self.headless = headless
        self._thread = None
        self._stop_event = threading.Event()
        self._current_profile = None
        self._default_profile = None

    def start(self):
        if self._thread is not None and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        logger.info("Profile auto-switcher started (poll: %.1fs)", self.poll_interval)

    def stop(self):
        self._stop_event.set()
        if self._thread is not None:
            self._thread.join(timeout=5)
            self._thread = None
        logger.info("Profile auto-switcher stopped")

    def is_running(self):
        return self._thread is not None and self._thread.is_alive()

    def set_default_profile(self, profile_name):
        self._default_profile = profile_name

    def _load_profile(self, profile_name):
        """Load a profile INI and apply it to the device."""
        profile_file = os.path.join(self.profile_path, profile_name + ".ini")
        if not os.path.exists(profile_file):
            logger.warning("Profile not found: %s", profile_file)
            return False
        if self.headless:
            self.model.load(profile_file)
            self.model.flush_device()
            logger.info(
                "Auto-switch applied profile: %s\n\t%s",
                profile_name,
                _format_settings(self.model.data),
            )
        return True

    def _apply_profile(self, profile_name):
        """Switch to a profile and notify."""
        if profile_name == self._current_profile:
            return
        logger.info("Switching to profile: %s", profile_name)
        if self._load_profile(profile_name):
            self._current_profile = profile_name
            send_notification(
                "Oversteer — Profile changed", f"Switched to: {profile_name}"
            )
            if self.on_profile_change:
                self.on_profile_change(profile_name)

    def _revert_to_default(self):
        """Revert to DEFAULT profile when no game is running."""
        logger.info("Reverting to DEFAULT profile")
        if self.headless:
            default_file = os.path.join(self.profile_path, "DEFAULT.ini")
            if os.path.isfile(default_file):
                self.model.load(default_file)
            else:
                self.model.data = self.model.defaults.copy()
                self.model.profile = None
                self.model.update_from_device_settings()
            self.model.flush_device()
            logger.info("\t%s", _format_settings(self.model.data))
        if self.on_profile_change:
            self.on_profile_change(None)

    def _run(self):
        """Main watch loop."""
        while not self._stop_event.is_set():
            try:
                processes = get_running_processes()
                profile_map = load_profile_processes(self.profile_path)

                if not profile_map:
                    logger.debug("No profiles with game_processes configured")
                    self._stop_event.wait(self.poll_interval)
                    continue

                matched = detect_game(processes, profile_map)

                if matched:
                    self._apply_profile(matched)
                elif self._default_profile:
                    self._apply_profile(self._default_profile)
                elif self._current_profile is not None:
                    self._current_profile = None
                    self._revert_to_default()

            except Exception as e:
                logger.error("Auto-switch error: %s", e, exc_info=True)

            self._stop_event.wait(self.poll_interval)
