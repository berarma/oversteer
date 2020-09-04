import configparser
from evdev import InputDevice, categorize, ecodes
import glob
import locale as Locale
from locale import gettext as _
import logging
import signal
import subprocess
import sys
import threading
import time
from xdg.BaseDirectory import *
from .device_manager import DeviceManager
from .gtk_ui import GtkUi
from .model import Model
from .profile import Profile

class Gui:

    def __init__(self, application):
        self.app = application
        self.locale = ''
        self.check_permissions = True
        self.device_manager = self.app.device_manager
        self.grab_input = False
        self.model = None
        self.models = {}
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

        self.ui = GtkUi(self)
        self.ui.set_app_version(self.app.version)
        self.ui.set_app_icon(os.path.join(self.app.icondir, 'org.berarma.Oversteer.svg'))
        self.ui.set_languages(self.languages)

        self.ui.set_language(self.locale)
        self.ui.set_check_permissions(self.check_permissions)

        self.populate_window()

        if self.app.device is not None:
            self.ui.set_device_id(self.app.device.get_id())

        if self.app.args.profile is not None:
            profile_file = os.path.join(self.profile_path, self.app.args.profile + '.ini')
            if os.path.exists(profile_file):
                self.ui.set_profile(profile_file)

        self.ui.update()

        threading.Thread(target=self.input_thread, daemon = True).start()

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

    def populate_profiles(self):
        profiles = []
        for profile_file in glob.iglob(os.path.join(self.profile_path, "*.ini")):
            profiles.append(profile_file)
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

    def load_profile(self, profile_file):
        if profile_file == '':
            return

        profile = Profile()
        profile.load(profile_file)
        self.model.load_settings(profile.to_dict())
        self.ui.set_new_profile_name('')

    def save_profile(self, profile_file):
        if profile_file is None or profile_file == '':
            return

        if self.device is None:
            return

        profile = Profile(self.model.to_dict())
        profile.save(profile_file)

    def save_profile_as(self, profile_name):
        profile_file = os.path.join(self.profile_path, profile_name + '.ini')
        if os.path.exists(profile_file):
            if not self.ui.confirmation_dialog(_("This profile already exists. Are you sure?")):
                return
        self.save_profile(profile_file)
        self.populate_profiles()
        self.ui.set_profile(profile_file)

    def delete_profile(self, profile_file):
        if profile_file != '' and profile_file is not None:
            if self.ui.confirmation_dialog(_("This profile will be deleted, are you sure?")):
                os.remove(profile_file)
                self.populate_profiles()

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
