import configparser
import csv
from evdev import InputDevice, categorize, ecodes, ff
import glob
import locale as Locale
from locale import gettext as _
import logging
import shutil
import signal
import subprocess
import sys
from threading import Thread, Event
import time
from xdg.BaseDirectory import *
from .device_manager import DeviceManager
from .gtk_ui import GtkUi
from .model import Model
from .profile import Profile
from .test_chart import TestChart

class Gui:

    def __init__(self, application, argv):
        self.app = application
        self.locale = ''
        self.check_permissions = True
        self.device_manager = self.app.device_manager
        self.grab_input = False
        self.model = None
        self.models = {}
        self.test_running = False
        self.test_chart = None
        self.last_wheel_axis_value = 32768
        self.button_config = [
            -1,
            -1,
            -1,
            -1,
            -1,
            -1,
            -1,
            -1,
            -1,
        ]
        self.thrustmaster_ids = [
            'b66e',
        ]
        self.button_labels = [
            _("Activation Switch"),
            _("Set 270º"),
            _("Set 360º"),
            _("Set 540º"),
            _("Set 900º"),
            _("+10º"),
            _("-10º"),
            _("+90º"),
            _("-90º"),
        ]
        self.button_setup_step = False
        self.languages = [
            ('', _('System default')),
            ('ca_ES', _('Valencian')),
            ('en_US', _('English')),
            ('es_ES', _('Spanish')),
            ('gl_ES', _('Galician')),
            ('ru_RU', _('Russian')),
        ]

        signal.signal(signal.SIGINT, self.sig_int_handler)

        self.config_path = save_config_path('oversteer')

        self.load_preferences()

        self.profile_path = os.path.join(self.config_path, 'profiles')
        if not os.path.isdir(self.profile_path):
            os.makedirs(self.profile_path, 0o700)

        self.ui = GtkUi(self, argv)
        self.ui.set_app_version(self.app.version)
        self.ui.set_app_icon(os.path.join(self.app.icondir, 'org.berarma.Oversteer.svg'))
        self.ui.set_languages(self.languages)

        self.ui.set_language(self.locale)
        self.ui.set_check_permissions(self.check_permissions)

        self.populate_window()

        self.device = self.app.device
        if self.app.device is not None:
            self.ui.set_device_id(self.app.device.get_id())

        if self.app.args.profile is not None:
            self.ui.set_profile(self.app.args.profile)

        self.ui.update()

        Thread(target=self.input_thread, daemon = True).start()

        self.ui.main()

    def sig_int_handler(self, signal, frame):
        sys.exit(0)

    def install_udev_file(self):
        if not self.check_permissions:
            return
        while True:
            affirmative = self.ui.confirmation_dialog(_("You don't have the " +
                "required permissions to change your wheel settings. You can " +
                "fix it yourself by copying the {} file to the {} directory " +
                "and rebooting.").format(self.app.udev_file, self.app.target_dir) + "\n\n" +
                _("Do you want us to make this change for you?"))
            if affirmative:
                return_code = subprocess.call([
                    'pkexec',
                    '/bin/sh',
                    '-c',
                    'cp -f ' + self.app.udev_file + ' ' + self.app.target_dir + ' && ' +
                    'udevadm control --reload-rules && udevadm trigger',
                ])
                if return_code == 0:
                    self.ui.info_dialog(_("Permissions rules installed."),
                            _("In some cases, a system restart might be needed."))
                    break
                else:
                    answer = self.ui.confirmation_dialog(_("Error installing " +
                        "permissions rules. Please, try again and make sure you " +
                        "use the right password for the administrator user."))
                    if not answer:
                        break
            else:
                break

    def populate_devices(self):
        if self.device_manager.is_changed():
            device_list = []
            for device in self.device_manager.get_devices():
                if device.is_ready():
                    device_list.append((device.get_id(), device.name))
            self.ui.set_devices(device_list)
            if not device_list:
                self.model = Model(None, self.ui)
                self.model.flush_ui()

    def populate_profiles(self):
        profiles = []
        for profile_file in glob.iglob(os.path.join(self.profile_path, "*.ini")):
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

        if not self.device.check_permissions():
            self.install_udev_file()

        if self.device.get_id() in self.models:
            self.model = self.models[self.device.get_id()]
        else:
            self.model = Model(self.device, self.ui)
            self.models[self.device.get_id()] = self.model

        self.ui.set_modes(self.model.get_mode_list())
        self.model.flush_ui()

    def load_profile(self, profile_name):
        if profile_name is None or profile_name == '':
            return

        profile_file = os.path.join(self.profile_path, profile_name + '.ini')
        if not os.path.exists(profile_file):
            self.ui.info_dialog(_("Error opening profile"), _("The selected profile can't be loaded."))
            return

        profile = Profile()
        profile.load(profile_file)
        self.model.load_settings(profile.to_dict())
        self.ui.safe_call(self.model.save_reference_values)

    def save_profile(self, profile_name, check_exists = False):
        if self.device is None:
            return

        if profile_name is None or profile_name == '':
            return

        profile_file = os.path.join(self.profile_path, profile_name + '.ini')
        if check_exists:
            if os.path.exists(profile_file):
                if not self.ui.confirmation_dialog(_("This profile already exists. Are you sure?")):
                    raise Exception()
        profile = Profile(self.model.to_dict())
        profile.save(profile_file)
        self.model.save_reference_values()

    def rename_profile(self, current_name, new_name):
        current_file = os.path.join(self.profile_path, current_name + '.ini')
        new_file = os.path.join(self.profile_path, new_name + '.ini')
        os.rename(current_file, new_file)

    def delete_profile(self, profile_name):
        if profile_name != '' and profile_name is not None:
            profile_file = os.path.join(self.profile_path, profile_name + '.ini')
            if self.ui.confirmation_dialog(_("This profile will be deleted, are you sure?")):
                os.remove(profile_file)
            else:
                raise Exception()

    def import_profile(self, path):
        if not path.endswith('.ini'):
            raise Exception(_('Invalid extension.'))
        profile_name = os.path.splitext(os.path.basename(path))[0]
        profile_file = os.path.join(self.profile_path, profile_name + '.ini')
        if os.path.exists(profile_file):
            raise Exception(_('A profile with that name already exists.'))
        shutil.copyfile(path, profile_file)
        return profile_name

    def export_profile(self, profile_name, path):
        profile_file = os.path.join(self.profile_path, profile_name + '.ini')
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
                self.button_config = list(map(int, config['DEFAULT']['button_config'].split(',')))

    def set_locale(self, locale):
        if locale is None:
            locale = ''
        if locale != '':
            try:
                Locale.setlocale(Locale.LC_ALL, (locale, 'UTF-8'))
                self.locale = locale
            except Locale.Error:
                self.ui.info_dialog(_("Failed to change language."),
                _("Make sure locale '" + str(locale) + ".UTF8' is generated on your system" ))
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
            'button_config': ','.join(map(str, self.button_config)),
        }
        config_file = os.path.join(self.config_path, 'config.ini')
        with open(config_file, 'w') as file:
            config.write(file)

    def stop_button_setup(self):
        self.button_setup_step = False
        self.ui.reset_define_buttons_text()

    def start_stop_button_setup(self):
        if self.button_setup_step is not False:
            self.stop_button_setup()
        else:
            self.button_setup_step = 0
            self.ui.set_define_buttons_text(self.button_labels[self.button_setup_step])

    def on_close_preferences(self):
        self.stop_button_setup()

    def on_button_press(self, button, value):
        if self.button_setup_step is not False:
            if value == 1 and (self.button_setup_step != 0 or button < 100):
                self.button_config[self.button_setup_step] = button
                self.button_setup_step = self.button_setup_step + 1
                if self.button_setup_step >= len(self.button_config):
                    self.stop_button_setup()
                    self.save_preferences()
                else:
                    self.ui.set_define_buttons_text(self.button_labels[self.button_setup_step])
            return

        if self.model.get_use_buttons():
            if button == self.button_config[0] and value == 0:
                device = self.device.get_input_device()
                if self.grab_input:
                    device.ungrab()
                    self.grab_input = False
                    self.ui.safe_call(self.ui.update_overlay, False)
                else:
                    device.grab()
                    self.grab_input = True
                    self.ui.safe_call(self.ui.update_overlay, True)
            if self.grab_input and value == 1:
                if button == self.button_config[1]:
                    self.ui.safe_call(self.model.ui_set_range, 270)
                if button == self.button_config[2]:
                    self.ui.safe_call(self.model.ui_set_range, 360)
                if button == self.button_config[3]:
                    self.ui.safe_call(self.model.ui_set_range, 540)
                if button == self.button_config[4]:
                    self.ui.safe_call(self.model.ui_set_range, 900)
                if button == self.button_config[5]:
                    self.ui.safe_call(self.add_range, 10)
                if button == self.button_config[6]:
                    self.ui.safe_call(self.add_range, -10)
                if button == self.button_config[7]:
                    self.ui.safe_call(self.add_range, 90)
                if button == self.button_config[8]:
                    self.ui.safe_call(self.add_range, -90)

    def add_range(self, delta):
        range = self.model.get_range()
        range = range + delta
        if range < 40:
            range = 40
        if range > 900:
            range = 900
        self.model.ui_set_range(range)

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
                    if self.test_running:
                        if not self.test_startup:
                            self.test_values.append((event.timestamp() - self.test_starttime, (event.value - 32768) / 32768))
                    else:
                        self.ui.safe_call(self.ui.set_steering_input, event.value)
                elif event.code == ecodes.ABS_Y:
                    self.ui.safe_call(self.ui.set_accelerator_input, event.value)
                elif event.code == ecodes.ABS_Z:
                    self.ui.safe_call(self.ui.set_brakes_input, event.value)
                elif event.code == ecodes.ABS_RZ:
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
                else:
                    delay = 100
                if event.code >= 288 and event.code <= 303:
                    button = event.code - 288
                if event.code >= 704 and event.code <= 712:
                    button = event.code - 688
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
            if self.device_manager.is_changed():
                self.ui.safe_call(self.populate_devices)

    def start_test(self):
        Thread(target=self.test_thread).start()

    def test_thread(self):
        self.test_startup = True
        self.test_running = True
        input_device = self.device.get_input_device()

        self.ui.test_container_stack.set_visible_child(self.ui.test_chart_running)

        # Save wheel settings
        current_range = self.device.get_range()
        current_ff_gain = self.device.get_ff_gain()
        current_autocenter = self.device.get_autocenter()

        # Prepare wheel
        try:
            for effect_id in range(input_device.ff_effects_count):
                input_device.erase_effect(effect_id)
        except OSError as e:
            pass
        self.device.set_range(900)
        self.device.set_ff_gain(65535)
        self.device.set_autocenter(0)

        turn_right = ff.Effect(
            ecodes.FF_CONSTANT, -1, 0x4000,
            ff.Trigger(0, 0),
            ff.Replay(0, 0),
            ff.EffectType(ff_constant_effect=ff.Constant(level=0x7fff))
        )
        right_force_id = input_device.upload_effect(turn_right)

        turn_left = ff.Effect(
            ecodes.FF_CONSTANT, -1, 0xc000,
            ff.Trigger(0, 0),
            ff.Replay(0, 0),
            ff.EffectType(ff_constant_effect=ff.Constant(level=0x7fff))
        )
        left_force_id = input_device.upload_effect(turn_left)

        input_device.write(ecodes.EV_FF, left_force_id, 1)
        time.sleep(0.1)
        input_device.write(ecodes.EV_FF, left_force_id, 0)
        self.device.set_autocenter(65535)
        time.sleep(1)
        self.device.set_autocenter(0)
        time.sleep(0.1)

        starting_wheel_pos = (self.last_wheel_axis_value - 32768) / 32768
        test_inputs = [(0, 0)]
        self.test_values = [(0, starting_wheel_pos)]
        self.test_starttime = time.time()
        time.sleep(0.1)
        self.test_startup = False

        test_inputs.append((time.time() - self.test_starttime, 1))
        input_device.write(ecodes.EV_FF, left_force_id, 1)
        time.sleep(0.3)
        input_device.write(ecodes.EV_FF, left_force_id, 0)

        test_inputs.append((time.time() - self.test_starttime, -1))
        input_device.write(ecodes.EV_FF, right_force_id, 1)
        time.sleep(0.3)
        input_device.write(ecodes.EV_FF, right_force_id, 0)

        test_inputs.append((time.time() - self.test_starttime, 1))
        input_device.write(ecodes.EV_FF, left_force_id, 1)
        time.sleep(0.3)
        input_device.write(ecodes.EV_FF, left_force_id, 0)
        test_inputs.append((time.time() - self.test_starttime, 0))

        time.sleep(0.5)

        test_inputs.append((time.time() - self.test_starttime, 0))

        self.test_running = False

        input_device.erase_effect(right_force_id)
        input_device.erase_effect(left_force_id)

        # Restore wheel settings
        self.device.set_range(current_range)
        self.device.set_ff_gain(current_ff_gain)
        self.device.set_autocenter(current_autocenter)

        self.test_chart = TestChart(test_inputs, self.test_values)

        if self.test_chart.latency() is None:
            self.ui.error_dialog(_('Steering wheel not responding.'), _('No wheel movement could be registered.'))
            return

        self.ui.safe_call(self.show_test_results)

    def show_test_results(self):
        self.ui.test_max_velocity.set_text(format(self.test_chart.max_velocity(), '.0f'))
        self.ui.test_latency.set_text(format(1000 * self.test_chart.latency(), '.0f'))
        self.ui.test_max_accel.set_text(format(self.test_chart.max_accel(), '.0f'))
        self.ui.test_max_decel.set_text(format(self.test_chart.max_decel(), '.0f'))
        self.ui.test_time_to_max_accel.set_text(format(1000 * self.test_chart.time_to_max_accel(), '.0f'))
        self.ui.test_time_to_max_decel.set_text(format(1000 * self.test_chart.time_to_max_decel(), '.0f'))
        self.ui.test_mean_accel.set_text(format(self.test_chart.mean_accel(), '.0f'))
        self.ui.test_mean_decel.set_text(format(self.test_chart.mean_decel(), '.0f'))
        self.ui.test_residual_decel.set_text(format(self.test_chart.residual_decel(), '.0f'))
        self.ui.test_estimated_snr.set_text(format(self.test_chart.estimated_snr(), '.0f'))

        self.ui.test_container_stack.set_visible_child(self.ui.test_chart_results)
        self.ui.on_test_ready()

    def import_test_values(self):
        filename = self.ui.file_chooser(_('CSV file to import'), 'open')
        if filename is None:
            return

        with open(filename) as csv_file:
            test_inputs = []
            test_values = []
            csv_reader = csv.reader(csv_file, delimiter=',')
            for row in csv_reader:
                if row[0].startswith('#'):
                    continue
                test_inputs.append((float(row[0]), float(row[1])))
                test_values.append((float(row[2]), float(row[3])))

        self.test_chart = TestChart(test_inputs, test_values)

        self.show_test_results()

        self.ui.info_dialog(_("Test data imported."),
            _("New test data imported from CSV file."))

    def export_test_values(self):
        if self.test_chart is None:
            return

        filename = self.ui.file_chooser(_('CSV file to export'), 'save', 'report.csv')
        if filename is None:
            return

        with open(filename, mode='w') as csv_file:
            csv_writer = csv.writer(csv_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            for v1, v2 in zip(self.test_chart.get_input_values(), self.test_chart.get_pos_values()):
                csv_writer.writerow([format(v1[0], '.5f'), format(v1[1], '.5f'), format(v2[0], '.5f'), format(v2[1], '.5f')])

        self.ui.info_dialog(_("Test data imported."),
            _("Current test data has been exported to a CSV file."))

    def open_test_chart(self):
        if self.test_chart is None:
            return

        canvas = self.test_chart.get_canvas()
        toolbar = self.test_chart.get_navigation_toolbar(canvas, self.ui.window)
        self.ui.show_test_chart(canvas, toolbar)

