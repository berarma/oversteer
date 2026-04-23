import configparser
import csv
from datetime import datetime
from evdev import ecodes
import glob
import locale as Locale
from locale import gettext as _
import logging
import os
import shutil
import signal
import subprocess
import sys
from threading import Thread
import time
from xdg.BaseDirectory import save_config_path
from .gtk_ui import GtkUi
from .model import Model
from .test import Test
from .combined_chart import CombinedChart
from .linear_chart import LinearChart
from .performance_chart import PerformanceChart
from .profile_auto_switcher import ProfileAutoSwitcher
from .auto_switch_ui import setup_auto_switch_widgets


class Gui:
    button_labels = [
        _("Press toggle button/s"),
        _("Press button to set 270°"),
        _("Press button to set 360°"),
        _("Press button to set 540°"),
        _("Press button to set 900°"),
        _("Press button for +10°"),
        _("Press button for -10°"),
        _("Press button for +90°"),
        _("Press button for -90°"),
    ]

    languages = [
        ("", _("System default")),
        ("en_US", _("English")),
        ("gl_ES", _("Galician")),
        ("ru_RU", _("Russian")),
        ("es_ES", _("Spanish")),
        ("ca_ES", _("Catalan")),
        ("tr_TR", _("Turkish")),
        ("fi_FI", _("Finnish")),
        ("de_DE", _("German")),
        ("pl_PL", _("Polish")),
        ("hu_HU", _("Hungarian")),
    ]

    def __init__(self, application, model, argv):
        self.app = application
        self.locale = ""
        self.check_permissions = True
        self.model = model
        self.device_manager = self.app.device_manager
        self.device = None
        self.grab_input = False
        self.test = None
        self.linear_chart = None
        self.performance_chart = None
        self.combined_chart = None
        self.button_setup_step = False
        self.button_config = [-1] * 9
        self.button_config[0] = [-1]
        self.pressed_button_count = 0
        self.auto_switcher = None

        signal.signal(signal.SIGINT, self.sig_int_handler)

        self.config_path = save_config_path("oversteer")

        self.load_preferences()

        if not os.path.isdir(self.app.profile_path):
            os.makedirs(self.app.profile_path, 0o700)

        self.ui = GtkUi(self, argv)
        self.ui.set_app_version(self.app.version)
        self.ui.set_app_icon(os.path.join(self.app.icondir, "oversteer.svg"))
        self.ui.set_languages(self.languages)
        self.ui.set_language(self.locale)
        self.ui.set_check_permissions(self.check_permissions)
        self.model.set_ui(self.ui)

        self.device_manager.start(self.device_changed)
        self.populate_window()

        self.ui.start()

        self.load_profile("DEFAULT")

        # Inject auto-switch widgets into Tools tab
        from .gtk_handlers import GtkHandlers

        handlers = GtkHandlers(self.ui, self)
        setup_auto_switch_widgets(self.ui, handlers)

        # Restore auto-switch state from preferences
        if self.auto_switch_enabled:
            self.ui.auto_switch_switch.set_state(True)
            self.start_auto_switch()

        self.ui.main()

    def sig_int_handler(self, signal, frame):
        self.stop_auto_switch()
        self.ui.quit()

    def device_changed(self):
        self.ui.safe_call(self.populate_window)

    def populate_window(self):
        devices = []
        for device in self.device_manager.get_devices():
            devices.append([device.id, device.name])
        self.ui.set_devices(devices)

        if not self.device_manager.get_devices():
            self.ui.set_profiles([])
            return

        if self.device is not None:
            self.device.close()

        self.device = self.device_manager.first_device()
        if not self.device:
            return

        self.model.set_device(self.device)
        self.model.flush_ui()

        profiles = []
        if os.path.isdir(self.app.profile_path):
            for filename in os.listdir(self.app.profile_path):
                if filename.endswith(".ini"):
                    profiles.append(filename[:-4])
        self.ui.set_profiles(profiles)
        self.ui.set_profile("DEFAULT")

    def load_preferences(self):
        config = configparser.ConfigParser()
        config.read(os.path.join(self.config_path, "preferences.ini"))
        if "DEFAULT" in config:
            self.locale = config["DEFAULT"].get("locale", "")
            self.check_permissions = bool(
                int(config["DEFAULT"].get("check_permissions", 1))
            )
            self.auto_switch_enabled = bool(
                int(config["DEFAULT"].get("auto_switch", 0))
            )

    def save_preferences(self):
        config = configparser.ConfigParser()
        config["DEFAULT"] = {
            "locale": self.locale,
            "check_permissions": int(self.check_permissions),
            "auto_switch": int(self.auto_switch_enabled),
        }
        with open(os.path.join(self.config_path, "preferences.ini"), "w") as configfile:
            config.write(configfile)

    def on_close_preferences(self):
        self.save_preferences()

    def set_check_permissions(self, state):
        self.check_permissions = state

    def set_locale(self, locale):
        self.locale = locale

    def change_device(self, device_id):
        device = self.device_manager.get_device_by_id(device_id)
        if device is None:
            return
        self.stop_auto_switch()
        self.device = device
        self.model.set_device(device)
        self.model.flush_ui()

    def load_profile(self, profile_name):
        if not profile_name:
            return
        if profile_name == "DEFAULT":
            profile_file = os.path.join(self.app.profile_path, "DEFAULT.ini")
            if os.path.isfile(profile_file):
                self.model.profile = None
                self.model.load(profile_file)
            else:
                self.model.data = self.model.defaults.copy()
                self.model.profile = None
                self.model.update_from_device_settings()
                self.model.save(profile_file)
            self.model.flush_ui()
            return
        profile_file = os.path.join(self.app.profile_path, profile_name + ".ini")
        self.model.load(profile_file)
        self.model.flush_ui()

    def save_profile(self, profile_name, new=False):
        if not profile_name:
            return
        profile_file = os.path.join(self.app.profile_path, profile_name + ".ini")
        if profile_name != "DEFAULT" and os.path.exists(profile_file) and new:
            raise Exception(_("This profile already exists."))
        self.model.save(profile_file)
        self.ui.set_profile(profile_name)

    def delete_profile(self, profile_name):
        if profile_name == "DEFAULT":
            raise Exception(_("The DEFAULT profile cannot be deleted."))
        profile_file = os.path.join(self.app.profile_path, profile_name + ".ini")
        if not os.path.exists(profile_file):
            raise Exception(_("This profile doesn't exist."))
        os.remove(profile_file)

    def rename_profile(self, source_name, target_name):
        if not target_name:
            raise Exception(_("Profile name cannot be empty."))
        source_file = os.path.join(self.app.profile_path, source_name + ".ini")
        target_file = os.path.join(self.app.profile_path, target_name + ".ini")
        if not os.path.exists(source_file):
            raise Exception(_("Source profile doesn't exist."))
        if os.path.exists(target_file):
            raise Exception(_("Target profile already exists."))
        os.rename(source_file, target_file)

    def import_profile(self, source_file):
        profile_name = os.path.splitext(os.path.basename(source_file))[0]
        target_file = os.path.join(self.app.profile_path, profile_name + ".ini")
        shutil.copy(source_file, target_file)
        return profile_name

    def export_profile(self, profile_name, target_file):
        profile_file = os.path.join(self.app.profile_path, profile_name + ".ini")
        shutil.copy(profile_file, target_file)

    def read_ffbmeter(self):
        if self.device is None:
            return 0
        return self.device.get_peak_ffb_level()

    def start_test(self):
        self.test = Test(self.device, self.model)
        self.test.set_ui(self.ui)
        self.test.start()

    def prev_test(self):
        if self.test is not None:
            self.test.prev()

    def run_test(self):
        if self.test is not None:
            self.test.run()

    def start_stop_button_setup(self):
        self.button_setup_step = True
        self.pressed_button_count = 0
        self.button_config = [-1] * 9
        self.button_config[0] = [-1]
        self.ui.set_define_buttons_text(self.button_labels[0])

    def button_pressed(self, code):
        if not self.button_setup_step:
            if self.device is None:
                return
            return
        if self.pressed_button_count == 0:
            self.button_config[0] = []
            if code not in self.button_config[0]:
                self.button_config[0].append(code)
        else:
            idx = self.pressed_button_count
            self.button_config[idx] = code
        self.pressed_button_count += 1
        if self.pressed_button_count >= len(self.button_labels):
            self.button_setup_step = False
            self.ui.reset_define_buttons_text()
            self.save_buttons_config()
        else:
            self.ui.set_define_buttons_text(
                self.button_labels[self.pressed_button_count]
            )

    def save_buttons_config(self):
        config = configparser.ConfigParser()
        config["buttons"] = {}
        for idx, button_config in enumerate(self.button_config):
            if isinstance(button_config, list):
                config["buttons"][f"action_{idx}"] = ",".join(map(str, button_config))
            else:
                config["buttons"][f"action_{idx}"] = str(button_config)
        config_path = os.path.join(self.config_path, "buttons.ini")
        with open(config_path, "w") as f:
            config.write(f)

    def start_app(self):
        args = self.app.args
        if args is not None and args.command:
            subprocess.Popen(args.command, shell=True)

    # --- Auto-switch integration ---

    def start_auto_switch(self):
        """Start the profile auto-switcher background thread."""
        if self.auto_switcher is not None and self.auto_switcher.is_running():
            return
        self.auto_switcher = ProfileAutoSwitcher(
            model=self.model,
            profile_path=self.app.profile_path,
            poll_interval=2.0,
            on_profile_change=lambda name: self.ui.safe_call(
                lambda n=name: self._on_auto_profile_change(n)
            ),
        )
        self.auto_switcher.start()
        self.auto_switch_enabled = True
        self.save_preferences()
        logging.info("Auto-switch started from GUI")

    def stop_auto_switch(self):
        """Stop the profile auto-switcher."""
        if self.auto_switcher is not None:
            self.auto_switcher.stop()
        self.auto_switcher = None
        self.auto_switch_enabled = False
        self.save_preferences()
        logging.info("Auto-switch stopped")

    def _on_auto_profile_change(self, profile_name):
        """Called (on main thread via safe_call) when auto-switch changes profile."""
        from .profile_auto_switcher import _format_settings

        if profile_name is None:
            self.load_profile("DEFAULT")
            logging.info("Auto-switch reverted to DEFAULT")
            return
        profile_file = os.path.join(self.app.profile_path, profile_name + ".ini")
        if not os.path.exists(profile_file):
            return
        self.model.profile = None
        self.model.load(profile_file)
        self.model.flush_device()
        self.ui.set_profile(profile_name)
        self.model.flush_ui()
        logging.info(
            "Auto-switch applied profile: %s\n\t%s",
            profile_name,
            _format_settings(self.model.data),
        )

    def open_test_chart(self):
        if self.combined_chart is None:
            return
        canvas = self.combined_chart.get_canvas()
        toolbar = self.combined_chart.get_navigation_toolbar(canvas)
        self.ui.show_test_chart(canvas, toolbar)

    def import_test_values(self):
        filename = self.ui.file_chooser(
            _("CSV file to import"), "open", file_type="csv"
        )
        if filename is None:
            return

        lin_input_values = []
        lin_output_values = []
        perf_input_values = []
        perf_output_values = []
        data_block = -1
        minimum_level = 0

        with open(filename, mode="r") as csv_file:
            csv_reader = csv.reader(csv_file)
            for row in csv_reader:
                if len(row) == 0:
                    continue
                if row[0] == "minimum_level":
                    minimum_level = float(row[1])
                elif row[0] == "linear_data":
                    data_block = 0
                elif row[0] == "performance_data":
                    data_block = 1
                elif data_block == 0:
                    lin_input_values.append((float(row[0]), float(row[1])))
                    lin_output_values.append((float(row[2]), float(row[3])))
                elif data_block == 1:
                    perf_input_values.append((float(row[0]), float(row[1])))
                    perf_output_values.append((float(row[2]), float(row[3])))

        self.linear_chart = LinearChart(
            lin_input_values, lin_output_values, self.device.get_max_range()
        )
        self.linear_chart.set_minimum_level(self.minimum_level)
        self.performance_chart = PerformanceChart(
            perf_input_values, perf_output_values, self.device.get_max_range()
        )
        self.combined_chart = CombinedChart(self.linear_chart, self.performance_chart)

        self.show_test_results()

        self.ui.info_dialog(
            _("Test data imported."), _("New test data imported from CSV file.")
        )

    def export_test_values(self):
        if self.combined_chart is None:
            return

        default_filename = "report-" + datetime.now().strftime("%Y%m%d%H%M%S") + ".csv"
        filename = self.ui.file_chooser(
            _("CSV file to export"), "save", default_filename, "csv"
        )
        if filename is None:
            return

        with open(filename, mode="w") as csv_file:
            csv_writer = csv.writer(
                csv_file, delimiter=",", quotechar='"', quoting=csv.QUOTE_MINIMAL
            )
            csv_writer.writerow(["minimum_level", self.minimum_level])
            csv_writer.writerow(["linear_data"])
            for v1, v2 in zip(
                self.linear_chart.get_input_values(),
                self.linear_chart.get_output_values(),
            ):
                csv_writer.writerow(
                    [
                        format(v1[0], ".5f"),
                        format(v1[1], ".5f"),
                        format(v2[0], ".5f"),
                        format(v2[1], ".5f"),
                    ]
                )
            csv_writer.writerow(["performance_data"])
            for v1, v2 in zip(
                self.performance_chart.get_input_values(),
                self.performance_chart.get_pos_values(),
            ):
                csv_writer.writerow(
                    [
                        format(v1[0], ".5f"),
                        format(v1[1], ".5f"),
                        format(v2[0], ".5f"),
                        format(v2[1], ".5f"),
                    ]
                )

        self.ui.info_dialog(
            _("Test data exported."),
            _("Current test data has been exported to a CSV file."),
        )
