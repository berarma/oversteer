from evdev import ecodes, InputDevice
import functools
import glob
import logging
import os
import pyudev
import re
import time

logging.basicConfig(level=logging.DEBUG)

class Wheels:

    supported_models = [
        'c24f', # G29
        'c262', # G920
        'c294', # Driving Force / Formula EX
        'c295', # MOMO
        'c298', # Driving Force pro
        'c299', # G25
        'c29a', # Driving Force GT
        'c29b', # G27
        'c29c', # Speed Force Wireless
        'ca03', # MOMO2
    ]

    def __init__(self):
        self.reset()

    def reset(self):
        self.devices = {}

        context = pyudev.Context()
        for device in context.list_devices(subsystem='input', ID_INPUT_JOYSTICK=1):
            if device.get('ID_VENDOR_ID') == '046d' and device.get('ID_MODEL_ID') in self.supported_models:
                self.add_udev_data(device)

        logging.debug('Devices:' + str(self.devices))

    def add_udev_data(self, device):
        device_id = device.get('ID_FOR_SEAT')

        if device_id not in self.devices:
            data = {'id': device_id}
            self.devices[device_id] = data
        else:
            data = self.devices[device_id]

        if device.get('DEVNAME'):
            if 'event' in device.get('DEVNAME'):
                data['dev'] = device.get('DEVNAME')
        else:
            data['path'] = os.path.join(device.sys_path, 'device')
            data['name'] = device.get('NAME').strip('"')

    def dev_to_id(self, dev):
        for device_id in self.devices:
            if self.devices[device_id]['dev'] == dev:
                return device_id
        return None

    def id_to_dev(self, device_id):
        return self.devices[device_id]['dev']

    def device_file(self, device_id, filename):
        return os.path.join(self.devices[device_id]['path'], filename)

    def checked_device_file(self, device_id, filename):
        path = self.device_file(device_id, filename)
        if not os.access(path, os.F_OK | os.R_OK | os.W_OK):
            return None
        return path

    def wait_for_device(self, device_id):
        context = pyudev.Context()
        monitor = pyudev.Monitor.from_netlink(context)
        monitor.filter_by('input')
        for device in iter(functools.partial(monitor.poll, 2), None):
            if device.action == 'add' and device.get('ID_FOR_SEAT') == device_id:
                self.add_udev_data(device)

    def first_device_id(self):
        return next(iter(self.devices))

    def get_devices(self):
        device_list = []
        for key, device in self.devices.items():
            device_list.append([key, device['name']])
        return device_list

    def get_alternate_modes(self, device_id):
        path = self.checked_device_file(device_id, "alternate_modes")
        if not path:
            return None
        with open(path, "r") as file:
            data = file.read()
        lines = data.splitlines()
        reg = re.compile("([^:]+): (.*)")
        alternate_modes = []
        for line in lines:
            matches = reg.match(line)
            mode_id = matches.group(1)
            if mode_id == "native":
                continue
            name = matches.group(2)
            if name.endswith("*"):
                name = name[:-2]
                selected = True
            else:
                selected = False
            alternate_modes.append([mode_id, name, selected])
        return alternate_modes

    def get_current_mode(self, device_id):
        path = self.checked_device_file(device_id, "alternate_modes")
        if not path:
            return None
        with open(path, "r") as file:
            data = file.read()
        lines = data.splitlines()
        reg = re.compile("([^:]+): (.*)")
        for line in lines:
            matches = reg.match(line)
            mode_id = matches.group(1)
            if mode_id == "native":
                continue
            name = matches.group(2)
            if name.endswith("*"):
                return mode_id
        return mode_id

    def get_range(self, device_id):
        path = self.checked_device_file(device_id, "range")
        if not path:
            return None
        with open(path, "r") as file:
            data = file.read()
        range = data.strip()
        return int(range)

    def get_combine_pedals(self, device_id):
        path = self.checked_device_file(device_id, "combine_pedals")
        if not path:
            return None
        with open(path, "r") as file:
            data = file.read()
        combine_pedals = data.strip()
        return int(combine_pedals)

    def get_autocenter(self, device_id):
        path = self.checked_device_file(device_id, "autocenter")
        if not path:
            return 0
        with open(path, "r") as file:
            data = file.read()
        autocenter = data.strip()
        return int(autocenter)

    def get_ff_gain(self, device_id):
        path = self.checked_device_file(device_id, "gain")
        if not path:
            return 100
        with open(path, "r") as file:
            data = file.read()
        gain = data.strip()
        return int(gain)

    def get_spring_level(self, device_id):
        path = self.checked_device_file(device_id, "spring_level")
        if not path:
            return None
        with open(path, "r") as file:
            data = file.read()
        spring_level = data.strip()
        return int(spring_level)

    def get_damper_level(self, device_id):
        path = self.checked_device_file(device_id, "damper_level")
        if not path:
            return None
        with open(path, "r") as file:
            data = file.read()
        damper_level = data.strip()
        return int(damper_level)

    def get_friction_level(self, device_id):
        path = self.checked_device_file(device_id, "friction_level")
        if not path:
            return None
        with open(path, "r") as file:
            data = file.read()
        friction_level = data.strip()
        return int(friction_level)

    def get_ffb_leds(self, device_id):
        path = self.checked_device_file(device_id, "ffb_leds")
        if not path:
            return None
        with open(path, "r") as file:
            data = file.read()
        ffb_leds = data.strip()
        return int(ffb_leds)

    def get_peak_ffb_level(self, device_id):
        path = self.checked_device_file(device_id, "peak_ffb_level")
        if not path:
            return None
        with open(path, "r") as file:
            data = file.read()
        peak_ffb_level = data.strip()
        return int(peak_ffb_level)

    def set_mode(self, device_id, emulation_mode):
        path = self.checked_device_file(device_id, "alternate_modes")
        if not path:
            return False
        old_mode = self.get_current_mode(device_id)
        if old_mode == emulation_mode:
            return True
        logging.debug("Setting mode: " + str(emulation_mode))
        with open(path, "w") as file:
            file.write(emulation_mode)
        self.wait_for_device(device_id)
        # Wait for self-calibration to finish
        time.sleep(3)
        return True

    def set_range(self, device_id, range):
        path = self.checked_device_file(device_id, "range")
        if not path:
            return False
        range = str(range)
        logging.debug("Setting range: " + range)
        with open(path, "w") as file:
            file.write(range)
        return True

    def set_combine_pedals(self, device_id, combine_pedals):
        path = self.checked_device_file(device_id, "combine_pedals")
        if not path:
            return False
        combine_pedals = str(combine_pedals)
        logging.debug("Setting combined pedals: " + combine_pedals)
        with open(path, "w") as file:
            file.write(combine_pedals)
        return True

    def set_autocenter(self, device_id, autocenter):
        autocenter = str(int(65535 * autocenter / 100))
        logging.debug("Setting autocenter strength: " + autocenter)
        path = self.checked_device_file(device_id, "autocenter")
        if path:
            with open(path, "w") as file:
                file.write(autocenter)
        else:
            dev = InputDevice(self.devices[device_id]['dev'])
            dev.write(ecodes.EV_FF, ecodes.FF_AUTOCENTER, int(autocenter))
        return True

    def set_ff_gain(self, device_id, gain):
        gain = str(int(65535 * gain / 100))
        logging.debug("Setting FF gain: " + gain)
        path = self.checked_device_file(device_id, "gain")
        if path:
            with open(path, "w") as file:
                file.write(gain)
        else:
            dev = InputDevice(self.devices[device_id]['dev'])
            dev.write(ecodes.EV_FF, ecodes.FF_GAIN, int(gain))

    def set_spring_level(self, device_id, level):
        path = self.checked_device_file(device_id, "spring_level")
        if not path:
            return False
        level = str(level)
        logging.debug("Setting spring level: " + level)
        with open(path, "w") as file:
            file.write(level)
        return True

    def set_damper_level(self, device_id, level):
        path = self.checked_device_file(device_id, "damper_level")
        if not path:
            return False
        level = str(level)
        logging.debug("Setting damper level: " + level)
        with open(path, "w") as file:
            file.write(level)
        return True

    def set_friction_level(self, device_id, level):
        path = self.checked_device_file(device_id, "friction_level")
        if not path:
            return False
        level = str(level)
        logging.debug("Setting friction level: " + level)
        with open(path, "w") as file:
            file.write(level)
        return True

    def set_ffb_leds(self, device_id, ffb_leds):
        path = self.checked_device_file(device_id, "ffb_leds")
        if not path:
            return False
        ffb_leds = str(ffb_leds)
        logging.debug("Setting FF leds: " + ffb_leds)
        with open(path, "w") as file:
            file.write(ffb_leds)
        return True

    def set_peak_ffb_level(self, device_id, peak_ffb_level):
        path = self.checked_device_file(device_id, "peak_ffb_level")
        if not path:
            return False
        peak_ffb_level = str(peak_ffb_level)
        logging.debug("Setting peak FF level: " + peak_ffb_level)
        with open(path, "w") as file:
            file.write(peak_ffb_level)
        return True

    def check_permissions(self, device_id):
        if not os.access(self.devices[device_id]['path'], os.F_OK | os.R_OK | os.X_OK):
            return False
        if not self.check_file_permissions(self.device_file(device_id, 'alternate_modes')):
            return False
        if not self.check_file_permissions(self.device_file(device_id, 'range')):
            return False
        if not self.check_file_permissions(self.device_file(device_id, 'combine_pedals')):
            return False
        if not self.check_file_permissions(self.device_file(device_id, 'gain')):
            return False
        if not self.check_file_permissions(self.device_file(device_id, 'autocenter')):
            return False
        if not self.check_file_permissions(self.device_file(device_id, 'spring_level')):
            return False
        if not self.check_file_permissions(self.device_file(device_id, 'damper_level')):
            return False
        if not self.check_file_permissions(self.device_file(device_id, 'friction_level')):
            return False
        if not self.check_file_permissions(self.device_file(device_id, 'ffb_leds')):
            return False
        if not self.check_file_permissions(self.device_file(device_id, 'peak_ffb_level')):
            return False
        return True

    def check_file_permissions(self, path):
        if path == None:
            return True
        if not os.access(path, os.F_OK):
            return True
        if os.access(path, os.R_OK | os.W_OK):
            return True
        return False

