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
        parser.add_argument('device_id', nargs='?', help=_("Device id"))
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

        from .wheels import Wheels
        wheels = Wheels()

        if args.device_id != None:
            device_id = args.device_id
            if os.path.exists(device_id):
                device_id = wheels.dev_to_id(os.path.realpath(device_id))
            if not wheels.check_permissions(device_id):
                print(_("You don't have the required permissions to change your " +
                    "wheel settings. You can fix it yourself by copying the {} " +
                    "file to the {} directory and rebooting.".format(udev_file,
                    target_dir)))
        else:
            device_id = wheels.first_device_id()
            args.device_id = device_id

        nothing_done = True
        if args.list == True:
            devices = wheels.get_devices()
            print(_("Devices found:"))
            for key, name in devices:
                print("  {}: {} ({})".format(wheels.id_to_dev(key), name, key))
            nothing_done = False
        if args.mode != None:
            wheels.set_mode(device_id, args.mode)
            nothing_done = False
        if args.range != None:
            wheels.set_range(device_id, args.range)
            nothing_done = False
        if args.combine_pedals != None:
            wheels.set_combine_pedals(device_id, args.combine_pedals)
            nothing_done = False
        if args.autocenter != None:
            wheels.set_autocenter(device_id, args.autocenter)
            nothing_done = False
        if args.ff_gain != None:
            wheels.set_ff_gain(device_id, args.ff_gain)
            nothing_done = False
        if args.spring_level != None:
            wheels.set_spring_level(device_id, args.spring_level)
            nothing_done = False
        if args.damper_level != None:
            wheels.set_damper_level(device_id, args.damper_level)
            nothing_done = False
        if args.friction_level != None:
            wheels.set_friction_level(device_id, args.friction_level)
            nothing_done = False
        if args.ffb_leds != None:
            wheels.set_ffb_leds(device_id, 1 if args.ffb_leds else 0)
            nothing_done = False
        if not args.interactive and args.profile != None:
            profile_file = os.path.join(save_config_path('oversteer'), 'profiles', args.profile + '.ini')
            profile = Profile()
            profile.load(profile_file)
            wheels.set_mode(device_id, profile.get_mode())
            wheels.set_range(device_id, profile.get_range())
            wheels.set_combine_pedals(device_id, profile.get_combine_pedals())
            wheels.set_autocenter(device_id, profile.get_autocenter())
            wheels.set_ff_gain(device_id, profile.get_ff_gain())
            wheels.set_spring_level(device_id, profile.get_spring_level())
            wheels.set_damper_level(device_id, profile.get_damper_level())
            wheels.set_friction_level(device_id, profile.get_friction_level())
            wheels.set_ffb_leds(device_id, profile.get_ffbmeter_leds())
            nothing_done = False
        if args.interactive or nothing_done:
            self.args = args
            self.wheels = wheels
            from oversteer.gui import Gui
            Gui(self)

        sys.exit(0)

