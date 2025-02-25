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
        ('', _('System default')),
        ('en_US', _('English')),
        ('gl_ES', _('Galician')),
        ('ru_RU', _('Russian')),
        ('es_ES', _('Spanish')),
        ('ca_ES', _('Valencian')),
        ('fi_FI', _('Finnish')),
        ('tr_TR', _('Turkish')),
        ('de_DE', _('German')),
        ('pl_PL', _('Polish')),
        ('hu_HU', _('Hungarian')),
    ]

    def __init__(self, application, model, argv):
        self.app = application
        self.locale = ''
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

        signal.signal(signal.SIGINT, self.sig_int_handler)

        self.config_path = save_config_path('oversteer')

        self.load_preferences()

        if not os.path.isdir(self.app.profile_path):
            os.makedirs(self.app.profile_path, 0o700)

        self.ui = GtkUi(self, argv)
        self.ui.set_app_version(self.app.version)
        self.ui.set_app_icon(os.path.join(self.app.icondir, 'io.github.berarma.Oversteer.svg'))
        self.ui.set_languages(self.languages)

        self.ui.set_language(self.locale)
        self.ui.set_check_permissions(self.check_permissions)

        self.models = {}

        self.ui.start()

        self.model.set_ui(self.ui)

        self.populate_window()

        if self.app.args.profile is not None:
            self.ui.set_profile(self.app.args.profile)

        start_manually = self.app.args.start_manually
        if start_manually is None:
            start_manually = self.model.get_start_app_manually()

        if not model.device:
            self.ui.info_dialog("No device available.")
            start_manually = True

        if self.app.args.command:
            if start_manually:
                self.ui.enable_start_app()
            else:
                self.start_app()

        Thread(target=self.input_thread, daemon = True).start()

        self.ui.main()

    def start_app(self):
        self.ui.disable_start_app()
        Thread(target=self.run_command).start() 

    def sig_int_handler(self, signal, frame):
        sys.exit(0)

    def install_udev_files(self):
        while True:
            affirmative = self.ui.confirmation_dialog(_("You don't have the " +
                "required permissions to change your wheel settings.") + "\n\n" + _("You can " +
                "fix it yourself by copying the files in {} to the {} directory " +
                "and rebooting.").format(self.app.udev_path, self.app.target_dir) + "\n\n" +
                _("Do you want us to make this change for you?"))
            if affirmative:
                copy_cmd = 'cp -f ' + self.app.udev_path + '* ' + self.app.target_dir + ' && '
                return_code = subprocess.call([
                    'pkexec',
                    '/bin/sh',
                    '-c',
                    copy_cmd +
                    'udevadm control --reload-rules && udevadm trigger',
                ])
                if return_code == 0:
                    self.ui.info_dialog(_("Permissions rules installed."),
                            _("In some cases, a system restart might be needed."))
                    break
                answer = self.ui.confirmation_dialog(_("Error installing " +
                    "permissions rules. Please, try again and make sure you " +
                    "use the right password for the administrator user."))
                if not answer:
                    break
            else:
                break

    def populate_devices(self):
        logging.debug("populate_devices")
        if self.device_manager.is_changed():
            device_list = []
            for device in self.device_manager.get_devices():
                if device.is_ready():
                    device_list.append((device.get_id(), device.name))
            self.ui.set_devices(device_list)

    def populate_profiles(self):
        profiles = []
        for profile_file in glob.iglob(os.path.join(self.app.profile_path, "*.ini")):
            profile_name = os.path.splitext(os.path.basename(profile_file))[0]
            profiles.append(profile_name)
        self.ui.set_profiles(profiles)

    def populate_window(self):
        self.populate_devices()
        self.populate_profiles()

    def change_device(self, device_id):
        self.device = self.device_manager.get_device(device_id)

        if self.device is None or not self.device.is_ready():
            return

        if not self.device.check_permissions() and self.check_permissions:
            if self.app.udev_path:
                self.install_udev_files()
            else:
                self.ui.info_dialog(_("You don't have the required permissions to change your wheel settings."))

        if not self.models:
            self.model.set_device(self.device)
            self.models[self.device.get_id()] = self.model
        if self.device.get_id() in self.models:
            self.model = self.models[self.device.get_id()]
        else:
            self.model = Model(self.device, self.ui)
            self.models[self.device.get_id()] = self.model

        self.ui.set_max_range(self.device.get_max_range())
        self.ui.set_modes(self.model.get_mode_list())

        if self.model.get_profile():
            self.ui.set_profile(self.model.get_profile())
        else:
            self.model.flush_device()
            self.model.flush_ui()

    def load_profile(self, profile_name):
        if profile_name is None or profile_name == '':
            return

        profile_file = os.path.join(self.app.profile_path, profile_name + '.ini')
        if not os.path.exists(profile_file):
            self.ui.info_dialog(_("Error opening profile"), _("The selected profile can't be loaded."))
            return

        self.model.load(profile_file)
        self.model.flush_device()
        self.model.flush_ui()

    def save_profile(self, profile_name, check_exists = False):
        if self.device is None:
            return

        if profile_name is None or profile_name == '':
            return

        profile_file = os.path.join(self.app.profile_path, profile_name + '.ini')
        if check_exists:
            if os.path.exists(profile_file):
                if not self.ui.confirmation_dialog(_("This profile already exists. Are you sure?")):
                    raise Exception()
        self.model.save(profile_file)

    def rename_profile(self, current_name, new_name):
        current_file = os.path.join(self.app.profile_path, current_name + '.ini')
        new_file = os.path.join(self.app.profile_path, new_name + '.ini')
        os.rename(current_file, new_file)

    def delete_profile(self, profile_name):
        if profile_name != '' and profile_name is not None:
            profile_file = os.path.join(self.app.profile_path, profile_name + '.ini')
            if self.ui.confirmation_dialog(_("This profile will be deleted, are you sure?")):
                os.remove(profile_file)
            else:
                raise Exception()

    def import_profile(self, path):
        if not path.endswith('.ini'):
            raise Exception(_('Invalid extension.'))
        profile_name = os.path.splitext(os.path.basename(path))[0]
        profile_file = os.path.join(self.app.profile_path, profile_name + '.ini')
        if os.path.exists(profile_file):
            raise Exception(_('A profile with that name already exists.'))
        shutil.copyfile(path, profile_file)
        return profile_name

    def export_profile(self, profile_name, path):
        profile_file = os.path.join(self.app.profile_path, profile_name + '.ini')
        if os.path.exists(path):
            if not self.ui.confirmation_dialog(_('File already exists, overwrite?')):
                raise Exception()
        shutil.copyfile(profile_file, path)

    def load_preferences(self):
        config = configparser.ConfigParser()
        config_file = os.path.join(self.config_path, 'config.ini')
        config.read(config_file)
        self.check_permissions = True
        if 'DEFAULT' in config:
            if 'locale' in config['DEFAULT'] and config['DEFAULT']['locale'] != '':
                self.locale = config['DEFAULT']['locale']
                Locale.setlocale(Locale.LC_ALL, (self.locale, 'UTF-8'))
            if 'check_permissions' in config['DEFAULT']:
                self.check_permissions = config['DEFAULT']['check_permissions'] == '1'
            if 'button_config' in config['DEFAULT'] and config['DEFAULT']['button_config'] != '':
                if 'button_toggle' not in config['DEFAULT']:
                    self.button_config = list(map(int, config['DEFAULT']['button_config'].split(',')))
                    self.button_config[0] = [self.button_config[0]]
                    self.save_preferences()
                else:
                    self.button_config[0] = list(map(int, config['DEFAULT']['button_toggle'].split(',')))
                    self.button_config[1:] = list(map(int, config['DEFAULT']['button_config'].split(',')))

    def set_locale(self, locale):
        if locale is None:
            locale = ''
        if locale != '':
            try:
                Locale.setlocale(Locale.LC_ALL, (locale, 'UTF-8'))
                self.locale = locale
            except Locale.Error:
                self.ui.info_dialog(_("Failed to change language"),
                _("Make sure locale '{}.UTF8' is generated on your system.").format(str(locale)))
                self.ui.set_language(self.locale)
        self.save_preferences()

    def set_check_permissions(self, check_permissions):
        self.check_permissions = check_permissions
        self.save_preferences()

    def save_preferences(self):
        config = configparser.ConfigParser()
        config['DEFAULT'] = {
            'locale': self.locale,
            'check_permissions': '1' if self.check_permissions else '0',
            'button_toggle': ','.join(map(str, self.button_config[0])),
            'button_config': ','.join(map(str, self.button_config[1:])),
        }
        config_file = os.path.join(self.config_path, 'config.ini')
        with open(config_file, 'w') as file:
            config.write(file)

    def stop_button_setup(self):
        self.button_setup_step = False
        self.pressed_button_count = 0
        self.ui.safe_call(self.ui.reset_define_buttons_text)

    def start_stop_button_setup(self):
        if self.button_setup_step is not False:
            self.stop_button_setup()
        else:
            self.button_setup_step = 0
            self.button_config = [-1] * 9
            self.pressed_button_count = 0
            self.ui.set_define_buttons_text(self.button_labels[self.button_setup_step])

    def on_close_preferences(self):
        self.stop_button_setup()

    def on_button_press(self, button, value):
        if self.button_setup_step is not False:
            if self.button_setup_step == 0:
                if button < 100:
                    if value == 1:
                        self.pressed_button_count += 1
                        if self.button_config[0] == -1:
                            self.button_config[0] = []
                        self.button_config[0].append(button)
                    else:
                        self.pressed_button_count -= 1
                        if self.pressed_button_count == 0:
                            self.button_setup_step += 1
                            self.ui.safe_call(self.ui.set_define_buttons_text, self.button_labels[self.button_setup_step])
                return
            if value == 1:
                self.button_config[self.button_setup_step] = button
                self.button_setup_step += 1
                if self.button_setup_step >= len(self.button_config):
                    self.stop_button_setup()
                    self.save_preferences()
                else:
                    self.ui.safe_call(self.ui.set_define_buttons_text, self.button_labels[self.button_setup_step])
            return

        if self.model.get_use_buttons():
            if self.grab_input and self.pressed_button_count == 0 and value == 1:
                if button == self.button_config[1]:
                    self.ui.safe_call(self.ui.set_range, 270)
                if button == self.button_config[2]:
                    self.ui.safe_call(self.ui.set_range, 360)
                if button == self.button_config[3]:
                    self.ui.safe_call(self.ui.set_range, 540)
                if button == self.button_config[4]:
                    self.ui.safe_call(self.ui.set_range, 900)
                if button == self.button_config[5]:
                    self.ui.safe_call(self.add_range, 10)
                if button == self.button_config[6]:
                    self.ui.safe_call(self.add_range, -10)
                if button == self.button_config[7]:
                    self.ui.safe_call(self.add_range, 90)
                if button == self.button_config[8]:
                    self.ui.safe_call(self.add_range, -90)
            if button in self.button_config[0]:
                if value == 1:
                    self.pressed_button_count += 1
                    if self.pressed_button_count == len(self.button_config[0]):
                        device = self.device.get_input_device()
                        if self.grab_input:
                            device.ungrab()
                            self.grab_input = False
                            self.ui.safe_call(self.ui.update_overlay, False)
                        else:
                            device.grab()
                            self.grab_input = True
                            self.ui.safe_call(self.ui.update_overlay, True)
                else:
                    self.pressed_button_count -= 1

    def add_range(self, delta):
        max_range = self.device.get_max_range()
        wrange = self.model.get_range()
        wrange = wrange + delta
        if wrange < 40:
            wrange = 40
        if wrange > max_range:
            wrange = max_range
        self.ui.set_range(wrange)

    def read_ffbmeter(self):
        level = self.device.get_peak_ffb_level()
        if level is None:
            return level
        level = int(level)
        if level > 0:
            self.device.set_peak_ffb_level(0)
        return level

    def process_events(self, events):
        for event in events:
            if event.type == ecodes.EV_ABS:
                if event.code == ecodes.ABS_X:
                    self.last_wheel_axis_value = event.value
                    if self.test and self.test.is_collecting_data():
                        self.test.append_data(event.timestamp(), event.value)
                    else:
                        self.ui.safe_call(self.ui.set_steering_input, event.value)
                elif event.code == ecodes.ABS_Z:
                    self.ui.safe_call(self.ui.set_accelerator_input, event.value)
                elif event.code == ecodes.ABS_RZ:
                    self.ui.safe_call(self.ui.set_brakes_input, event.value)
                elif event.code == ecodes.ABS_Y:
                    self.ui.safe_call(self.ui.set_clutch_input, event.value)
                elif event.code == ecodes.ABS_HAT0X:
                    self.ui.safe_call(self.ui.set_hatx_input, event.value)
                    if event.value == -1:
                        self.on_button_press(100, 1)
                    elif event.value == 1:
                        self.on_button_press(101, 1)
                elif event.code == ecodes.ABS_HAT0Y:
                    self.ui.safe_call(self.ui.set_haty_input, event.value)
                    if event.value == -1:
                        self.on_button_press(102, 1)
                    elif event.value == 1:
                        self.on_button_press(103, 1)
            if event.type == ecodes.EV_KEY:
                if event.value:
                    delay = 0
                    if self.test and self.test.is_awaiting_action():
                        self.test.trigger_action()
                else:
                    delay = 100

                button = None

                if event.code >= 288 and event.code <= 303:
                    button = event.code - 288
                if event.code >= 304 and event.code <= 316:
                    button = event.code - 304
                if event.code >= 704 and event.code <= 715:
                    button = event.code - 688

                if button is not None:
                    self.ui.safe_call(self.ui.set_btn_input, button, event.value, delay)
                    self.on_button_press(button, event.value)

    def input_thread(self):
        while 1:
            if self.device is not None and self.device.is_ready():
                try:
                    events = self.device.read_events(0.5)
                    if events is not None:
                        self.process_events(events)
                except OSError as e:
                    logging.debug(e)
                    time.sleep(1)
            else:
                time.sleep(1)
            self.ui.safe_call(self.populate_devices)

    def run_command(self):
        proc = subprocess.Popen(self.app.args.command, shell=True)
        returncode = proc.wait()
        if returncode != 0:
            self.ui.safe_call(self.ui.error_dialog, _('Command error'),
                _("The supplied command failed:\n{}").format(self.app.args.command[0]))
        else:
            self.ui.safe_call(self.ui.quit)

    def start_test(self):
        def test_callback(name = 'end'):
            if name == 'end':
                self.ui.safe_call(self.end_test)
            elif name == 'running':
                self.ui.safe_call(self.ui.show_test_running, self.test_run, 1)
        self.test = Test(self.device, test_callback)
        self.test_run = 0
        self.ui.switch_test_panel(self.test_run)

    def end_test(self):
        if self.test_run == 0:
            self.minimum_level = self.test.get_minimum_level()
        elif self.test_run == 1:
            self.linear_chart = LinearChart(self.test.get_input_values(), self.test.get_output_values(),
                    self.device.get_max_range())
            self.linear_chart.set_minimum_level(self.minimum_level)
        elif self.test_run == 2:
            self.performance_chart = PerformanceChart(self.test.get_input_values(), self.test.get_output_values(),
                    self.device.get_max_range())
            if self.performance_chart.get_latency() is None:
                self.ui.error_dialog(_('Steering wheel not responding.'), _('No wheel movement could be registered.'))
                self.ui.switch_test_panel(None)
                return
            self.combined_chart = CombinedChart(self.linear_chart, self.performance_chart)
            self.test = None
            self.test_run = None
            self.show_test_results()
            return
        self.next_test()

    def run_test(self):
        self.ui.show_test_running(self.test_run)
        self.test.run(self.test_run)

    def prev_test(self):
        self.test_run -= 1
        if self.test_run == -1:
            self.test_run = None
        self.ui.switch_test_panel(self.test_run)
        if self.test_run is None and self.combined_chart is not None:
            self.show_test_results()

    def next_test(self):
        self.test_run += 1
        self.ui.switch_test_panel(self.test_run)
        if self.test_run > 2:
            return

    def show_test_results(self):
        self.ui.test_latency.set_text(format(1000 * self.performance_chart.get_latency(), '.0f'))
        self.ui.test_max_velocity.set_text(format(self.performance_chart.get_max_velocity(), '.0f'))
        self.ui.test_max_accel.set_text(format(self.performance_chart.get_max_accel(), '.0f'))
        self.ui.test_max_decel.set_text(format(self.performance_chart.get_max_decel(), '.0f'))
        self.ui.test_time_to_max_accel.set_text(format(1000 * self.performance_chart.get_time_to_max_accel(), '.0f'))
        self.ui.test_time_to_max_decel.set_text(format(1000 * self.performance_chart.get_time_to_max_decel(), '.0f'))
        self.ui.test_mean_accel.set_text(format(self.performance_chart.get_mean_accel(), '.0f'))
        self.ui.test_mean_decel.set_text(format(self.performance_chart.get_mean_decel(), '.0f'))
        self.ui.test_residual_decel.set_text(format(self.performance_chart.get_residual_decel(), '.0f'))
        self.ui.test_estimated_snr.set_text(format(self.performance_chart.get_estimated_snr(), '.0f'))
        self.ui.test_minimum_level.set_text(format(self.linear_chart.get_minimum_level_percent(), '.1f'))
        self.ui.on_test_ready()

    def import_test_values(self):
        filename = self.ui.file_chooser(_('CSV file to import'), 'open', file_type='csv')
        if filename is None:
            return

        with open(filename) as csv_file:
            lin_input_values = []
            lin_output_values = []
            perf_input_values = []
            perf_output_values = []
            data_block = 0
            csv_reader = csv.reader(csv_file, delimiter=',')
            for row in csv_reader:
                if row[0].startswith('#'):
                    continue
                if row[0] == 'minimum_level':
                    self.minimum_level = row[1]
                elif row[0] == 'linear_data':
                    data_block = 0
                elif row[0] == 'performance_data':
                    data_block = 1
                elif data_block == 0:
                    lin_input_values.append((float(row[0]), float(row[1])))
                    lin_output_values.append((float(row[2]), float(row[3])))
                elif data_block == 1:
                    perf_input_values.append((float(row[0]), float(row[1])))
                    perf_output_values.append((float(row[2]), float(row[3])))

        self.linear_chart = LinearChart(lin_input_values, lin_output_values, self.device.get_max_range())
        self.linear_chart.set_minimum_level(self.minimum_level)
        self.performance_chart = PerformanceChart(perf_input_values, perf_output_values, self.device.get_max_range())
        self.combined_chart = CombinedChart(self.linear_chart, self.performance_chart)

        self.show_test_results()

        self.ui.info_dialog(_("Test data imported."),
            _("New test data imported from CSV file."))

    def export_test_values(self):
        if self.combined_chart is None:
            return

        default_filename = 'report-' + datetime.now().strftime('%Y%m%d%H%M%S') + '.csv'
        filename = self.ui.file_chooser(_('CSV file to export'), 'save', default_filename, 'csv')
        if filename is None:
            return

        with open(filename, mode='w') as csv_file:
            csv_writer = csv.writer(csv_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            csv_writer.writerow(['minimum_level', self.minimum_level])
            csv_writer.writerow(['linear_data'])
            for v1, v2 in zip(self.linear_chart.get_input_values(), self.linear_chart.get_output_values()):
                csv_writer.writerow([format(v1[0], '.5f'), format(v1[1], '.5f'), format(v2[0], '.5f'), format(v2[1], '.5f')])
            csv_writer.writerow(['performance_data'])
            for v1, v2 in zip(self.performance_chart.get_input_values(), self.performance_chart.get_pos_values()):
                csv_writer.writerow([format(v1[0], '.5f'), format(v1[1], '.5f'), format(v2[0], '.5f'), format(v2[1], '.5f')])

        self.ui.info_dialog(_("Test data exported."),
            _("Current test data has been exported to a CSV file."))

    def open_test_chart(self):
        if self.combined_chart is None:
            return

        canvas = self.combined_chart.get_canvas()
        toolbar = self.combined_chart.get_navigation_toolbar(canvas)
        self.ui.show_test_chart(canvas, toolbar)
