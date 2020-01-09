import argparse
import configparser
from locale import gettext as _
import logging
import os
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
        parser.add_argument('--range', type=int, help=_("set the rotation range (40-900)"))
        parser.add_argument('--combine-pedals', type=int, dest='combine_pedals', help=_("combine pedals (0-2)"))
        parser.add_argument('--autocenter', type=int, help=_("set the autocenter strength (0-100)"))
        parser.add_argument('--ff-gain', type=int, help=_("set the FF gain (0-100)"))
        parser.add_argument('--spring-level', type=int, help=_("set the spring level (0-100)"))
        parser.add_argument('--damper-level', type=int, help=_("set the damper level (0-100)"))
        parser.add_argument('--friction-level', type=int, help=_("set the friction level (0-100)"))
        parser.add_argument('--ffb-leds', action='store_true', help=_("enable/disable FFBmeter leds"))
        parser.add_argument('--ffb-overlay', action='store_true', help=_("enable/disable FFBmeter overlay"))
        parser.add_argument('--range-overlay', action='store_true', help=_("enable/disable wheel range overlay"))
        parser.add_argument('-p', '--profile', help=_("load settings from a profile"))
        parser.add_argument('-i', '--interactive', action='store_true', help=_("start the GUI"))
        parser.add_argument('--debug', action='store_true', help=_("enable debug output"))

        args = parser.parse_args(argv[1:])

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

        if args.list == True:
            devices = wheels.get_devices()
            print(_("Devices found:"))
            for key, name in devices:
                print("  {}: {} ({})".format(wheels.id_to_dev(key), name, key))
        if args.mode != None:
            wheels.set_mode(device_id, args.mode)
        if args.range != None:
            wheels.set_range(device_id, args.range)
        if args.combine_pedals != None:
            wheels.set_combine_pedals(device_id, args.combine_pedals)
        if args.autocenter != None:
            wheels.set_autocenter(device_id, args.autocenter)
        if args.ff_gain != None:
            wheels.set_ff_gain(device_id, args.ff_gain)
        if args.spring_level != None:
            wheels.set_spring_level(device_id, args.spring_level)
        if args.damper_level != None:
            wheels.set_damper_level(device_id, args.damper_level)
        if args.friction_level != None:
            wheels.set_friction_level(device_id, args.friction_level)
        if args.ffb_leds != None and args.ffb_leds:
            wheels.set_ffb_leds(device_id, 1)
        if args.ffb_overlay != None and args.ffb_overlay:
            args.interactive = True
        if args.range_overlay != None and args.range_overlay:
            args.interactive = True
        if args.profile != None:
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
        if args.interactive or len(sys.argv) == 1:
            self.args = args
            self.wheels = wheels
            from oversteer.gui import Gui
            Gui(self)

        sys.exit(0)

