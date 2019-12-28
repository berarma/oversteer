import argparse
import configparser
from locale import gettext as _
import os
import sys
from xdg.BaseDirectory import *

class Application:
    def __init__(self, version, pkgdatadir):
        self.version = version
        self.datadir = pkgdatadir

    def run(self, argv):
        if len(argv) == 1:
            from .gtk_ui import GtkUi
            GtkUi(self.version, self.datadir)
        else:
            parser = argparse.ArgumentParser(prog=argv[0], description=_("Oversteer - Steering Wheel Manager"))
            parser.add_argument('device_id', nargs='?', help=_("Device id"))
            parser.add_argument('--list', action='store_true', help=_("list connected devices"))
            parser.add_argument('--mode', help=_("set the compatibility mode"))
            parser.add_argument('--range', type=int, help=_("set the rotation range"))
            parser.add_argument('--combine-pedals', dest='combine_pedals', default=None, action='store_true', help=_("combine pedals"))
            parser.add_argument('--no-combine-pedals', dest='combine_pedals', action='store_false')
            parser.add_argument('--autocenter-strength', type=int, help=_("set the autocenter strength"))
            parser.add_argument('--ff-gain', type=int, help=_("set the FF gain"))
            parser.add_argument('--profile', help=_("load settings from a profile"))

            args = parser.parse_args(argv[1:])

            from .wheels import Wheels
            wheels = Wheels()

            if args.device_id != None:
                device_id = args.device_id
                if os.path.exists(device_id):
                    device_id = wheels.device_name_to_id(os.path.realpath(device_id))

            if args.list == True:
                devices = wheels.get_devices()
                print(_("Devices found:"))
                for key, name in devices:
                    print("    {} ({})".format(name, key))
            if args.mode != None:
                wheels.set_mode(device_id, args.mode)
            if args.range != None:
                wheels.set_range(device_id, args.range)
            if args.combine_pedals != None:
                wheels.set_combine_pedals(device_id, args.combine_pedals)
            if args.autocenter_strength != None:
                wheels.set_autocenter_strength(device_id, args.autocenter_strength)
            if args.ff_gain != None:
                wheels.set_ff_gain(device_id, args.ff_gain)
            if args.profile != None:
                profile_path = os.path.join(save_config_path('oversteer'), 'profiles', args.profile + '.ini')
                defaults = {
                    'autocenter_strength': 0,
                    'ff_gain': 0,
                }
                config = configparser.ConfigParser(defaults)
                config.read(profile_path)
                wheels.set_mode(device_id, config.get('default', 'mode'))
                wheels.set_range(device_id, int(config.get('default', 'range')))
                wheels.set_combine_pedals(device_id, True if config.get('default', 'combine_pedals') == 'True' else False)
                wheels.set_autocenter_strength(device_id, int(config.get('default', 'autocenter_strength')))
                wheels.set_ff_gain(device_id, int(config.get('default', 'ff_gain')))

            sys.exit(0)

