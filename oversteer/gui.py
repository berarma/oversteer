import configparser
from evdev import InputDevice, categorize, ecodes
import glob
import locale
from locale import gettext as _
import select
import signal
import subprocess
import sys
import threading
import time
from xdg.BaseDirectory import *
from .wheels import Wheels
from .gtk_ui import GtkUi
from .profiles import Profile

class Gui:

    device = None

    languages = [
        ('', _('System default')),
        ('en_US', _('English')),
        ('es_ES', _('Spanish')),
        ('gl_ES', _('Galician')),
    ]

    def __init__(self, application):
        self.app = application
        self.wheels = self.app.wheels

        signal.signal(signal.SIGINT, self.sig_int_handler)

        self.config_path = save_config_path('oversteer')

        config = configparser.ConfigParser()
        config_file = os.path.join(self.config_path, 'config.ini')
        config.read(config_file)
        self.check_permissions_dialog = True
        if 'base' in config:
            if 'locale' in config['base'] and config['base']['locale'] != '':
                locale.setlocale(locale.LC_ALL, (config['base']['locale'], 'UTF-8'))
            if 'check_permissions_dialog' in config['base']:
                self.check_permissions_dialog = config['base']['check_permissions_dialog']

        self.profile_path = os.path.join(self.config_path, 'profiles')
        if not os.path.isdir(self.profile_path):
            os.makedirs(self.profile_path, 0o700)

        self.ui = GtkUi(self)
        self.ui.set_app_version(self.app.version)
        self.ui.set_app_icon(os.path.join(self.app.icondir, 'org.berarma.Oversteer.svg'))
        self.ui.set_languages(self.languages)
        if 'base' in config and 'locale' in config['base']:
            self.ui.set_language(config['base']['locale'])
        else:
            self.ui.set_language('')

        self.ui.set_check_permissions(self.check_permissions_dialog)

        self.populate_window()

        if self.app.args.device_id:
            self.ui.set_device_id(self.app.args.device_id)

        if self.app.args.ffb_overlay or self.app.args.range_overlay:
            if self.app.args.ffb_overlay:
                self.ui.set_ffbmeter_overlay(True)
            if self.app.args.range_overlay:
                self.ui.set_range_overlay(True)
            self.ui.set_overlay(True)
            self.ui.window.iconify()

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
                "and rebooting.".format(udev_file, target_dir)) + "\n\n" +
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
        self.wheels.reset()
        self.populate_window()

    def populate_devices(self):
        devices = []
        for pair in self.wheels.get_devices():
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

    def read_settings(self, device_id, ignore_emulation_mode = False):
        alternate_modes = self.wheels.get_alternate_modes(device_id);
        self.ui.set_emulation_modes(alternate_modes)

        emulation_mode = self.wheels.get_current_mode(device_id)
        if not ignore_emulation_mode:
            self.ui.set_emulation_mode(emulation_mode)
            self.ui.change_emulation_mode(emulation_mode)

        if emulation_mode == 'G29':
            self.steering_input_multiplier = 1
        else:
            self.steering_input_multiplier = 4

        range = self.wheels.get_range(device_id)
        self.ui.set_range(range)
        self.ui.set_range_overlay_visibility(True if range else False)

        combine_pedals = self.wheels.get_combine_pedals(device_id)
        self.ui.set_combine_pedals(combine_pedals)

        autocenter = self.wheels.get_autocenter(device_id)
        self.ui.set_autocenter(autocenter)

        ff_gain = self.wheels.get_ff_gain(device_id)
        self.ui.set_ff_gain(ff_gain)

        spring_level = self.wheels.get_spring_level(device_id)
        self.ui.set_spring_level(spring_level)

        damper_level = self.wheels.get_damper_level(device_id)
        self.ui.set_damper_level(damper_level)

        friction_level = self.wheels.get_friction_level(device_id)
        self.ui.set_friction_level(friction_level)

        ffb_leds = self.wheels.get_ffb_leds(device_id)
        self.ui.set_ffbmeter_leds(ffb_leds)

        self.ui.set_ffbmeter_overlay_visibility(True if self.wheels.get_peak_ffb_level(device_id) != None else False)

    def change_device(self, device_id):
        if device_id == None:
            self.device = None
            return

        self.device = InputDevice(self.wheels.id_to_dev(device_id))

        if not self.wheels.check_permissions(device_id):
            self.install_udev_file()

        self.read_settings(device_id)


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
        if profile.get_range_overlay() != None:
            self.ui.set_range_overlay(profile.get_range_overlay())
        if profile.get_overlay() != None:
            self.ui.set_overlay(profile.get_overlay())
        self.ui.set_new_profile_name('')

    def save_profile(self, profile_file):
        if profile_file == None or profile_file == '':
            return

        profile = Profile()
        profile.set_mode(self.ui.get_emulation_mode())
        profile.set_range(self.ui.get_range())
        profile.set_combine_pedals(self.ui.get_combine_pedals())
        profile.set_autocenter(self.ui.get_autocenter())
        profile.set_ff_gain(self.ui.get_ff_gain())
        profile.set_spring_level(self.ui.get_spring_level())
        profile.set_damper_level(self.ui.get_damper_level())
        profile.set_friction_level(self.ui.get_friction_level())
        profile.set_ffbmeter_leds(self.ui.get_ffbmeter_leds())
        profile.set_ffbmeter_overlay(self.ui.get_ffbmeter_overlay())
        profile.set_range_overlay(self.ui.get_range_overlay())
        profile.set_overlay(self.ui.get_overlay())
        profile.save(profile_file)
        self.populate_profiles()
        self.ui.set_profile(profile_file)

    def save_profile_as(self, profile_name):
        profile_file = os.path.join(self.profile_path, profile_name + '.ini')
        if os.path.exists(profile_file):
            if not self.ui.confirmation_dialog(_("This profile already exists. Are you sure?")):
                return
        self.save_profile(profile_file)

    def set_emulation_mode(self, device_id, mode):
        self.device = None
        self.wheels.set_mode(device_id, mode)
        self.device = InputDevice(self.wheels.id_to_dev(device_id))
        self.ui.set_device_id(device_id)
        self.read_settings(device_id, True)

    def change_range(self, device_id, range):
        self.wheels.set_range(device_id, range)

    def combine_none(self, device_id):
        self.wheels.set_combine_pedals(device_id, 0)

    def combine_brakes(self, device_id):
        self.wheels.set_combine_pedals(device_id, 1)

    def combine_clutch(self, device_id):
        self.wheels.set_combine_pedals(device_id, 2)

    def set_ff_gain(self, device_id, ff_gain):
        self.wheels.set_ff_gain(device_id, ff_gain)

    def set_spring_level(self, device_id, level):
        self.wheels.set_spring_level(device_id, level)

    def set_damper_level(self, device_id, level):
        self.wheels.set_damper_level(device_id, level)

    def set_friction_level(self, device_id, level):
        self.wheels.set_friction_level(device_id, level)

    def ffbmeter_leds(self, device_id, state):
        self.wheels.set_ffb_leds(device_id, 1 if state else 0)

    def change_autocenter(self, device_id, autocenter):
        self.wheels.set_autocenter(device_id, autocenter)

    def delete_profile(self, profile_file):
        if profile_file != '' and profile_file != None:
            if self.ui.confirmation_dialog(_("This profile will be deleted, are you sure?")):
                os.remove(profile_file)
                self.populate_profiles()

    def apply_preferences(self):
        language = self.ui.get_language()
        if language == None:
            language = ''
        self.check_permissions_dialog = self.ui.get_check_permissions()
        check_permissions = '1' if self.check_permissions_dialog else '0'
        config = configparser.ConfigParser()
        config['base'] = {
            'locale': language,
            'check_permissions': check_permissions,
        }
        config_file = os.path.join(self.config_path, 'config.ini')
        with open(config_file, 'w') as file:
            config.write(file)
        if language != '':
            locale.setlocale(locale.LC_ALL, (language, 'UTF-8'))

    def read_ffbmeter(self, device_id):
        level = self.wheels.get_peak_ffb_level(device_id)
        if level == None:
            return level
        level = int(level)
        if level > 0:
            self.wheels.set_peak_ffb_level(device_id, 0)
        return level

    def read_events(self, device):
        for event in device.read():
            if event.type == ecodes.EV_ABS:
                if event.code == ecodes.ABS_X:
                    value = event.value * self.steering_input_multiplier
                    self.ui.set_steering_input(value)
                elif event.code == ecodes.ABS_Y:
                    self.ui.set_clutch_input(event.value)
                elif event.code == ecodes.ABS_Z:
                    self.ui.set_accelerator_input(event.value)
                elif event.code == ecodes.ABS_RZ:
                    self.ui.set_brakes_input(event.value)
                elif event.code == ecodes.ABS_HAT0X:
                    self.ui.set_hatx_input(event.value)
                elif event.code == ecodes.ABS_HAT0Y:
                    self.ui.set_haty_input(event.value)
            if event.type == ecodes.EV_KEY:
                if event.code >= 288 and event.code <= 303:
                    self.ui.set_btn_input(event.code - 288, event.value)
                if event.code >= 704 and event.code <= 712:
                    self.ui.set_btn_input(event.code - 704 + 16, event.value)

    def input_thread(self):
        while 1:
            if self.device != None:
                devices = {self.device.fd: self.device}
                while 1:
                    r, w, x = select.select(devices, [], [], 0.2)
                    try:
                        for fd in r:
                            self.read_events(devices[fd])
                    except OSError:
                        break;
            time.sleep(1);

