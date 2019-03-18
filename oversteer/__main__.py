import argparse
import configparser
from oversteer.gtk_ui import GtkUi
import locale
from locale import gettext as _
import sys
from oversteer.wheels import Wheels
from xdg.BaseDirectory import *

locale.bindtextdomain('oversteer', 'po')
locale.textdomain('oversteer')
locale.setlocale(locale.LC_ALL, '')

if len(sys.argv) == 1:
    GtkUi()
else:
    parser = argparse.ArgumentParser(description=_("Oversteer - Steering Wheel Manager"))
    parser.add_argument('device_id', nargs='?', help=_("Device id"))
    parser.add_argument('--list', action='store_true', help=_("list connected devices"))
    parser.add_argument('--mode', help=_("set the compatibility mode"))
    parser.add_argument('--range', type=int, help=_("set the rotation range"))
    parser.add_argument('--combine-pedals', dest='combine_pedals', default=None, action='store_true', help=_("combine pedals"))
    parser.add_argument('--no-combine-pedals', dest='combine_pedals', action='store_false')

    args = parser.parse_args()

    wheels = Wheels()

    device_id = args.device_id

    if args.list != None:
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

    sys.exit(0)

