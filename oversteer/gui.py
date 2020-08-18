import configparser
from evdev import InputDevice, categorize, ecodes
import glob
import locale
from locale import gettext as _
import signal
import subprocess
import sys
import threading
import time
from xdg.BaseDirectory import *
from .device_manager import DeviceManager
from .gtk_ui import GtkUi
from .profiles import Profile

class Gui:

    def __init__(self, application):
        self.app = application
        self.device_manager = self.app.device_manager
        self.locale = ''
        self.device = None
        self.grab_input = False
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
            ('en_US', _('English')),
            ('es_ES', _('Spanish')),
            ('gl_ES', _('Galician')),
            ('ca_ES', _('Valencian')),
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

        self.ui.set_check_permissions(self.check_permissions_dialog)

        self.populate_window()

        if self.app.device:
            self.device = self.app.device
            self.ui.set_device_id(self.device.get_id())

        if self.app.args.profile != None:
            profile_file = os.path.join(self.profile_path, self.app.args.profile + '.ini')
            if os.path.exists(profile_file):
                self.ui.set_profile(profile_file)

        threading.Thread(target=self.input_thread, daemon = True).start()

        self.ui.main()

    def sig_int_handler(self, signal, frame):
        sys.exit(0)

    def install_udev_file(self):
        if not self.check_permissions_dialog:
            return
        udev_file = self.app.datadir + '/udev/99-logitech-wheel-perms.rules'
        target_dir = '/etc/udev/rules.d/'
        while True:
            affirmative = self.ui.confirmation_dialog(_("You don't have the " +
                "required permissions to change your wheel settings. You can " +
                "fix it yourself by copying the {} file to the {} directory " +
                "and rebooting.").format(udev_file, target_dir) + "\n\n" +
                _("Do you want us to make this change for you?"))
            if affirmative:
                return_code = subprocess.call([
                    'pkexec',
                    '/bin/sh',
                    '-c',
                    'cp -f ' + udev_file + ' ' + target_dir + ' && ' +
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

    def update(self):
        self.device = None
        self.device_manager.reset()
        self.populate_window()

    def populate_devices(self):
        devices = []
        for pair in self.device_manager.list_devices():
            devices.append(pair)
        self.ui.set_devices(devices)

    def populate_profiles(self):
        profiles = []
        for profile_file in glob.iglob(os.path.join(self.profile_path, "*.ini")):
            profiles.append(profile_file)
        self.ui.set_profiles(profiles)

    def populate_window(self):
        self.populate_devices()
        self.populate_profiles()
        self.ui.update()

    def read_settings(self, ignore_emulation_mode = False):
        alternate_modes = self.device.list_modes()
        self.ui.set_emulation_modes(alternate_modes, True)

        emulation_mode = self.device.get_mode()
        if not ignore_emulation_mode:
            self.ui.set_emulation_mode(emulation_mode)
            self.ui.change_emulation_mode(emulation_mode)

        range = self.device.get_range()
        self.ui.set_range(range, True)
        if range != None:
            # The range returned by the driver after an emulation mode change can be wrong
            self.device.set_range(range)

        combine_pedals = self.device.get_combine_pedals()
        self.ui.set_combine_pedals(combine_pedals, True)

        autocenter = self.device.get_autocenter()
        self.ui.set_autocenter(autocenter)

        ff_gain = self.device.get_ff_gain()
        self.ui.set_ff_gain(ff_gain)

        spring_level = self.device.get_spring_level()
        self.ui.set_spring_level(spring_level, True)

        damper_level = self.device.get_damper_level()
        self.ui.set_damper_level(damper_level, True)

        friction_level = self.device.get_friction_level()
        self.ui.set_friction_level(friction_level, True)

        ffb_leds = self.device.get_ffb_leds()
        self.ui.set_ffbmeter_leds(ffb_leds, True)

        self.ui.set_ffbmeter_overlay_visibility(True if self.device.get_peak_ffb_level() != None else False)

    def change_device(self, device_id):
        self.device = self.device_manager.get_device(device_id)

        if not self.device.check_permissions():
            self.install_udev_file()

        self.read_settings()

        self.ui.set_ffbmeter_overlay(False)
        self.ui.set_wheel_range_overlay('never')

    def load_profile(self, profile_file):
        if profile_file == '':
            return
        profile = Profile()
        profile.load(profile_file)
        if profile.get_mode() != None:
            self.ui.set_emulation_mode(profile.get_mode())
            self.ui.change_emulation_mode(profile.get_mode())
        if profile.get_range() != None:
            self.ui.set_range(profile.get_range())
        if profile.get_combine_pedals() != None:
            self.ui.set_combine_pedals(profile.get_combine_pedals())
        if profile.get_autocenter() != None:
            self.ui.set_autocenter(profile.get_autocenter())
        if profile.get_ff_gain() != None:
            self.ui.set_ff_gain(profile.get_ff_gain())
        if profile.get_spring_level() != None:
            self.ui.set_spring_level(profile.get_spring_level())
        if profile.get_damper_level() != None:
            self.ui.set_damper_level(profile.get_damper_level())
        if profile.get_friction_level() != None:
            self.ui.set_friction_level(profile.get_friction_level())
        if profile.get_ffbmeter_leds() != None:
            self.ui.set_ffbmeter_leds(profile.get_ffbmeter_leds())
        if profile.get_ffbmeter_overlay() != None:
            self.ui.set_ffbmeter_overlay(profile.get_ffbmeter_overlay())
        if profile.get_wheel_range_overlay() != None:
            self.ui.set_wheel_range_overlay(profile.get_wheel_range_overlay())
        if profile.get_wheel_buttons() != None:
            self.ui.set_wheel_buttons(profile.get_wheel_buttons())
        self.ui.set_new_profile_name('')

    def save_profile(self, profile_file):
        if profile_file == None or profile_file == '':
            return

        profile = Profile()
        profile.set_ffbmeter_overlay(self.ui.get_ffbmeter_overlay())
        profile.set_wheel_range_overlay(self.ui.get_wheel_range_overlay())
        profile.set_wheel_buttons(self.ui.get_wheel_buttons())
        profile.save(profile_file)
        self.populate_profiles()
        self.ui.set_profile(profile_file)

    def save_profile_as(self, profile_name):
        profile_file = os.path.join(self.profile_path, profile_name + '.ini')
        if os.path.exists(profile_file):
            if not self.ui.confirmation_dialog(_("This profile already exists. Are you sure?")):
                return
        self.save_profile(profile_file)

    def set_emulation_mode(self, mode):
        self.device.set_mode(mode)
        self.emulation_mode = mode
        self.ui.set_device_id(self.device.get_id())
        self.read_settings(True)

    def change_range(self, range):
        self.device.set_range(range)

    def combine_none(self):
        self.device.set_combine_pedals(0)

    def combine_brakes(self):
        self.device.set_combine_pedals(1)

    def combine_clutch(self):
        self.device.set_combine_pedals(2)

    def set_ff_gain(self, ff_gain):
        self.device.set_ff_gain(ff_gain)

    def set_spring_level(self, level):
        self.device.set_spring_level(level)

    def set_damper_level(self, level):
        self.device.set_damper_level(level)

    def set_friction_level(self, level):
        self.device.set_friction_level(level)

    def ffbmeter_leds(self, state):
        self.device.set_ffb_leds(1 if state else 0)

    def change_autocenter(self, autocenter):
        self.device.set_autocenter(autocenter)

    def delete_profile(self, profile_file):
        if profile_file != '' and profile_file != None:
            if self.ui.confirmation_dialog(_("This profile will be deleted, are you sure?")):
                os.remove(profile_file)
                self.populate_profiles()

    def load_preferences(self):
        config = configparser.ConfigParser()
        config_file = os.path.join(self.config_path, 'config.ini')
        config.read(config_file)
        self.check_permissions_dialog = True
        if 'DEFAULT' in config:
            if 'locale' in config['DEFAULT'] and config['DEFAULT']['locale'] != '':
                self.locale = config['DEFAULT']['locale']
                locale.setlocale(locale.LC_ALL, (self.locale, 'UTF-8'))
            if 'check_permissions' in config['DEFAULT']:
                self.check_permissions_dialog = config['DEFAULT']['check_permissions'] == '1'
            if 'button_config' in config['DEFAULT'] and config['DEFAULT']['button_config'] != '':
                self.button_config = list(map(int, config['DEFAULT']['button_config'].split(',')))

    def save_preferences(self):
        language = self.ui.get_language()
        if language == None:
            language = ''
        self.check_permissions_dialog = self.ui.get_check_permissions()
        check_permissions = '1' if self.check_permissions_dialog else '0'
        config = configparser.ConfigParser()
        if language != '':
            try:
                locale.setlocale(locale.LC_ALL, (language, 'UTF-8'))
            except locale.Error:
                self.ui.info_dialog(_("Failed to change language."),
                _("Make sure locale '" + str(language) + ".UTF8' is generated on your system" ))
                self.ui.set_language(self.locale)
                language = self.ui.get_language()
        config['DEFAULT'] = {
            'locale': language,
            'check_permissions': check_permissions,
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

        if self.ui.get_wheel_buttons_enabled():
            if button == self.button_config[0] and value == 0:
                device = self.device.get_input_device()
                if self.grab_input:
                    device.ungrab()
                    self.grab_input = False
                    self.ui.update_overlay(False)
                else:
                    device.grab()
                    self.grab_input = True
                    self.ui.update_overlay(True)
            if self.grab_input and value == 1:
                if button == self.button_config[1]:
                    self.ui.set_range(270)
                if button == self.button_config[2]:
                    self.ui.set_range(360)
                if button == self.button_config[3]:
                    self.ui.set_range(540)
                if button == self.button_config[4]:
                    self.ui.set_range(900)
                if button == self.button_config[5]:
                    self.add_range(10)
                if button == self.button_config[6]:
                    self.add_range(-10)
                if button == self.button_config[7]:
                    self.add_range(90)
                if button == self.button_config[8]:
                    self.add_range(-90)

    def read_ffbmeter(self):
        level = self.device.get_peak_ffb_level()
        if level == None:
            return level
        level = int(level)
        if level > 0:
            self.device.set_peak_ffb_level(0)
        return level

    def add_range(self, delta):
        range = self.ui.get_range()
        range = range + delta
        if range < 40:
            range = 40
        if range > 900:
            range = 900
        self.ui.set_range(range)

    def process_events(self, events):
        for event in events:
            if event.type == ecodes.EV_ABS:
                if event.code == ecodes.ABS_X:
                    self.ui.set_steering_input(event.value)
                elif event.code == ecodes.ABS_Y:
                    self.ui.set_accelerator_input(event.value)
                elif event.code == ecodes.ABS_Z:
                    self.ui.set_brakes_input(event.value)
                elif event.code == ecodes.ABS_RZ:
                    self.ui.set_clutch_input(event.value)
                elif event.code == ecodes.ABS_HAT0X:
                    self.ui.set_hatx_input(event.value)
                    if event.value == -1:
                        self.on_button_press(100, 1)
                    elif event.value == 1:
                        self.on_button_press(101, 1)
                elif event.code == ecodes.ABS_HAT0Y:
                    self.ui.set_haty_input(event.value)
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
                self.ui.set_btn_input(button, event.value, delay)
                self.on_button_press(button, event.value)

    def input_thread(self):
        while 1:
            if self.device is not None:
                try:
                    events = self.device.read_events(0.2)
                    if events != None:
                        self.process_events(events)
                except OSError as e:
                    print(e)
                    time.sleep(1)
            else:
                time.sleep(1)

