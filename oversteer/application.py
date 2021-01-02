import argparse
from locale import gettext as _
import logging
import os
from oversteer.gui import Gui
from .device_manager import DeviceManager
from .model import Model
import sys
from xdg.BaseDirectory import save_config_path

class Application:

    def __init__(self, version, pkgdatadir, icondir):
        self.version = version
        self.datadir = pkgdatadir
        self.icondir = icondir
        self.udev_file = self.datadir + '/udev/99-logitech-wheel-perms.rules'
        self.target_dir = '/etc/udev/rules.d/'

    def run(self, argv):
        parser = argparse.ArgumentParser(prog=argv[0], description=_("Oversteer - Steering Wheel Manager"))
        parser.add_argument('command', nargs='*', help=_("Run as companion of command"))
        parser.add_argument('--device', help=_("Device path"))
        parser.add_argument('--list', action='store_true', help=_("list connected devices"))
        parser.add_argument('--mode', help=_("set the compatibility mode"))
        parser.add_argument('--range', type=int, help=_("set the rotation range [40-900]"))
        parser.add_argument('--combine-pedals', type=int, dest='combine_pedals', help=_("combine pedals [0-2]"))
        parser.add_argument('--autocenter', type=int, help=_("set the autocenter strength [0-100]"))
        parser.add_argument('--ff-gain', type=int, help=_("set the FF gain [0-100]"))
        parser.add_argument('--spring-level', type=int, help=_("set the spring level [0-100]"))
        parser.add_argument('--damper-level', type=int, help=_("set the damper level [0-100]"))
        parser.add_argument('--friction-level', type=int, help=_("set the friction level [0-100]"))
        parser.add_argument('--ffb-leds', action='store_true', default=None, help=_("enable FFBmeter leds"))
        parser.add_argument('--no-ffb-leds', dest='ffb_leds', action='store_false', default=None, help=_("disable FFBmeter leds"))
        parser.add_argument('--center-wheel', action='store_true', default=None, help=_("center wheel"))
        parser.add_argument('--remove-deadzones', action='store_true', default=None, help=_("remove dead zones"))
        parser.add_argument('-p', '--profile', help=_("load settings from a profile"))
        parser.add_argument('-g', '--gui', action='store_true', help=_("start the GUI"))
        parser.add_argument('--debug', action='store_true', help=_("enable debug output"))
        parser.add_argument('--version', action='store_true', help=_("show version"))

        args = parser.parse_args(argv[1:])
        argc = len(sys.argv[1:])

        if args.version:
            print("Oversteer v" + self.version)
            sys.exit(0)

        if not args.debug:
            logging.disable(level=logging.INFO)

        device_manager = DeviceManager()
        device_manager.start()

        if args.list:
            argc -= 1
            devices = device_manager.get_devices()
            print(_("Devices found:"))
            for device in devices:
                print("  {}: {}".format(device.dev_name, device.name))
            sys,exit(0)

        if args.device is not None:
            argc -= 1
            if os.path.exists(args.device):
                device = device_manager.get_device(os.path.realpath(args.device))
                if not device.check_permissions():
                    print(_(("You don't have the required permissions to change your " +
                        "wheel settings. You can fix it yourself by copying the {} " +
                        "file to the {} directory and rebooting.").format(self.udev_file,
                        self.target_dir)))
        else:
            device = device_manager.first_device()

        start_gui = args.gui or argc == 0

        if device is None and not start_gui:
            print(_("No device available."))
            sys.exit(1)

        model = Model(device)

        if args.profile is not None:
            profile_file = os.path.join(save_config_path('oversteer'), 'profiles', args.profile + '.ini')
            if not os.path.exists(profile_file):
                print(_("This profile doesn't exist."))
                sys.exit(2)
            model.load(profile_file)
        if args.mode is not None:
            model.set_mode(args.mode)
        if args.range is not None:
            model.set_range(args.range)
        if args.combine_pedals is not None:
            model.set_combine_pedals(args.combine_pedals)
        if args.autocenter is not None:
            model.set_autocenter(args.autocenter)
        if args.ff_gain is not None:
            model.set_ff_gain(args.ff_gain)
        if args.spring_level is not None:
            model.set_spring_level(args.spring_level)
        if args.damper_level is not None:
            model.set_damper_level(args.damper_level)
        if args.friction_level is not None:
            model.set_friction_level(args.friction_level)
        if args.ffb_leds is not None:
            model.set_ffb_leds(1 if args.ffb_leds else 0)
        if args.center_wheel is not None:
            model.set_center_wheel(True)
        if args.remove_deadzones is not None:
            model.set_remove_deadzones(True)
        if start_gui:
            self.args = args
            self.device_manager = device_manager
            Gui(self, model, argv)
