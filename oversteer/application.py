import argparse
import configparser
from locale import gettext as _
import logging
import os
from .profiles import Profile
import sys
from xdg.BaseDirectory import *

class Application:
    def __init__(self, version, pkgdatadir, icondir):
        self.version = version
        self.datadir = pkgdatadir
        self.icondir = icondir

    def run(self, argv):
        parser = argparse.ArgumentParser(prog=argv[0], description=_("Oversteer - Steering Wheel Manager"))
        parser.add_argument('device_path', nargs='?', help=_("Device path"))
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
        parser.add_argument('-p', '--profile', help=_("load settings from a profile"))
        parser.add_argument('-i', '--interactive', action='store_true', help=_("start the GUI"))
        parser.add_argument('--debug', action='store_true', help=_("enable debug output"))
        parser.add_argument('--version', action='store_true', help=_("show version"))

        args = parser.parse_args(argv[1:])

        if args.version:
            print("Oversteer v" + self.version)
            sys.exit(0)

        if not args.debug:
            logging.basicConfig(level=logging.WARNING)

        from .device_manager import DeviceManager
        device_manager = DeviceManager()

        if args.device_path is not None:
            if os.path.exists(args.device_path):
                device = device_manager.get_device(os.path.realpath(args.device_path))
            if not device.check_permissions():
                print(_("You don't have the required permissions to change your " +
                    "wheel settings. You can fix it yourself by copying the {} " +
                    "file to the {} directory and rebooting.".format(udev_file,
                    target_dir)))
        else:
            device = device_manager.first_device()

        nothing_done = True
        if args.list == True:
            device_list = device_manager.list_devices()
            print(_("Devices found:"))
            for id, name in device_list:
                device = device_manager.get_device(id)
                print("  {}: {}".format(device.dev_name, name))
            nothing_done = False
        if args.mode != None:
            device.set_mode(args.mode)
            nothing_done = False
        if args.range != None:
            device.set_range(args.range)
            nothing_done = False
        if args.combine_pedals != None:
            device.set_combine_pedals(args.combine_pedals)
            nothing_done = False
        if args.autocenter != None:
            device.set_autocenter(args.autocenter)
            nothing_done = False
        if args.ff_gain != None:
            device.set_ff_gain(args.ff_gain)
            nothing_done = False
        if args.spring_level != None:
            device.set_spring_level(args.spring_level)
            nothing_done = False
        if args.damper_level != None:
            device.set_damper_level(args.damper_level)
            nothing_done = False
        if args.friction_level != None:
            device.set_friction_level(args.friction_level)
            nothing_done = False
        if args.ffb_leds != None:
            device.set_ffb_leds(1 if args.ffb_leds else 0)
            nothing_done = False
        if not args.interactive and args.profile != None:
            profile_file = os.path.join(save_config_path('oversteer'), 'profiles', args.profile + '.ini')
            profile = Profile()
            profile.load(profile_file)
            device.load_settings(profile.export_settings())
            nothing_done = False
        if args.interactive or nothing_done:
            self.args = args
            self.device_manager = device_manager
            self.device = device
            from oversteer.gui import Gui
            Gui(self)

        sys.exit(0)

