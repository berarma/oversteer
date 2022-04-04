import argparse
from locale import gettext as _
import logging
import os
import subprocess
from .device_manager import DeviceManager
from .model import Model
import sys
from xdg.BaseDirectory import save_config_path

class Application:

    def __init__(self, version, pkgdatadir, icondir):
        self.version = version
        self.datadir = pkgdatadir
        self.icondir = icondir
        self.udev_path = self.datadir + '/udev/'
        self.target_dir = '/etc/udev/rules.d/'
        self.profile_path = os.path.join(save_config_path('oversteer'), 'profiles')
        self.device_manager = None

        if not os.path.isdir(self.udev_path):
            self.udev_path = None

    def apply_args(self, model, args):
        if not model.device:
            device = None
            if args.device is not None:
                if os.path.exists(args.device):
                    device = self.device_manager.get_device(os.path.realpath(args.device))
                    if device and not device.check_permissions():
                        if self.udev_path:
                            print(_("You don't have the required permissions to change your wheel settings.") + " " +
                                    _("You can fix it yourself by copying the files in {} to the {} directory and rebooting.")
                                    .format(self.udev_path, self.target_dir))
                        else:
                            print(_("You don't have the required permissions to change your wheel settings."))
            else:
                device = self.device_manager.first_device()

            if not device:
                print(_("No device available."))
                return

            model.set_device(device)

        if args.profile is not None:
            profile_file = os.path.join(self.profile_path, args.profile + '.ini')
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
            model.set_center_wheel(1 if args.center_wheel else 0)

    def run(self, argv):
        parser = argparse.ArgumentParser(prog=argv[0], description=_("Oversteer - Steering Wheel Manager"))
        parser.add_argument('command', nargs='*', help=_("Run as command's companion"))
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
        parser.add_argument('--no-center-wheel', dest='center_wheel', action='store_false', default=None, help=_("don't center wheel"))
        parser.add_argument('--start-manually', action='store_true', default=None, help=_("run command manually"))
        parser.add_argument('--no-start-manually', dest='start_manually', action='store_false', default=None,
                help=_("don't run command manually"))
        parser.add_argument('-p', '--profile', help=_("load settings from a profile"))
        parser.add_argument('-g', '--gui', action='store_true', help=_("start the GUI"))
        parser.add_argument('--debug', action='store_true', help=_("enable debug output"))
        parser.add_argument('--version', action='store_true', help=_("show version"))

        args = parser.parse_args(argv[1:])
        argc = len(sys.argv[1:])

        if args.version:
            print("Oversteer v" + self.version)
            sys.exit(0)

        if args.debug:
            argc -= 1
        else:
            logging.disable(level=logging.INFO)

        self.device_manager = DeviceManager()
        self.device_manager.start()


        if args.list:
            argc -= 1
            devices = self.device_manager.get_devices()
            print(_("Devices found:"))
            for device in devices:
                print("  {}: {}".format(device.dev_name, device.name))
            sys.exit(0)

        if args.profile is not None:
            profile_file = os.path.join(self.profile_path, args.profile + '.ini')
            if not os.path.exists(profile_file):
                print(_("This profile doesn't exist."))
                exit(-1)

        if args.device is not None:
            argc -= 1

        start_gui = args.gui or argc == 0

        if start_gui:
            self.args = args
            from oversteer.gui import Gui
            Gui(self, argv)
        else:
            model = Model()
            self.apply_args(model, args)
            if args.command:
                subprocess.Popen(args.command, shell=True)

