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
        self.devices = {}

        context = pyudev.Context()
        for device in context.list_devices(subsystem='input', ID_INPUT_JOYSTICK=1):
            if device.get('ID_VENDOR_ID') == '046d' and device.get('ID_MODEL_ID') in self.supported_models:
                self.register_device(device)

        logging.debug('Devices:' + str(self.devices))

    def register_device(self, device):
        device_id = device.get('ID_FOR_SEAT')

        if device_id not in self.devices:
            data = {'device_id': device_id}
            self.devices[device_id] = data
        else:
            data = self.devices[device_id]

        if device.get('DEVNAME'):
            if 'event' in device.get('DEVNAME'):
                data['devName'] = device.get('DEVNAME')
        else:
            data['devicePath'] = os.path.join(device.sys_path, 'device')
            data['name'] = device.get('NAME').strip('"')

    def device_name_to_id(self, device_name):
        for device_id in self.devices:
            if self.devices[device_id]['devName'] == device_name:
                return device_id
        return None

    def device_file(self, device_id, filename):
        return os.path.join(self.devices[device_id]['devicePath'], filename)

    def wait_for_device(self, device_id):
        context = pyudev.Context()
        monitor = pyudev.Monitor.from_netlink(context)
        monitor.filter_by('input')
        for device in iter(functools.partial(monitor.poll, 2), None):
            if device.action == 'add' and device.get('ID_FOR_SEAT') == device_id:
                self.register_device(device)

    def get_devices(self):
        device_list = []
        for key, device in self.devices.items():
            device_list.append([key, device['name']])
        return device_list

    def get_alternate_modes(self, device_id):
        path = self.device_file(device_id, "alternate_modes")
        if not os.path.isfile(path):
            return []
        with open(path, "r") as file:
            data = file.read()
        lines = data.splitlines()
        reg = re.compile("([^:]+): (.*)")
        alternate_modes = []
        for line in lines:
            matches = reg.match(line)
            id = matches.group(1)
            if id == "native":
                continue
            name = matches.group(2)
            if name.endswith("*"):
                name = name[:-2]
                selected = True
            else:
                selected = False
            alternate_modes.append([id, name, selected])
        return alternate_modes

    def get_range(self, device_id):
        path = self.device_file(device_id, "range")
        if not os.path.isfile(path):
            return 200
        with open(path, "r") as file:
            data = file.read()
        range = data.strip()
        return int(float(range))

    def get_combine_pedals(self, device_id):
        path = self.device_file(device_id, "combine_pedals")
        if not os.path.isfile(path):
            return False
        with open(path, "r") as file:
            data = file.read()
        combine_pedals = data.strip()
        return combine_pedals == '1'

    def set_mode(self, device_id, emulation_mode):
        path = self.device_file(device_id, "alternate_modes")
        if not os.path.isfile(path):
            return
        logging.debug("Setting mode: " + str(emulation_mode))
        with open(path, "w") as file:
            file.write(emulation_mode)
        self.wait_for_device(device_id)
        time.sleep(3)

    def set_range(self, device_id, range):
        path = self.device_file(device_id, "range")
        if not os.path.isfile(path):
            return
        logging.debug("Setting range: " + str(range))
        with open(path, "w") as file:
            file.write(str(range))

    def set_combine_pedals(self, device_id, combine_pedals):
        path = self.device_file(device_id, "combine_pedals")
        if not os.path.isfile(path):
            return
        logging.debug("Setting combined pedals: " + str(combine_pedals))
        with open(path, "w") as file:
            file.write("1" if combine_pedals else "0")

    def set_autocenter_strength(self, device_id, strength):
        dev = InputDevice(self.devices[device_id]['devName'])
        autocenter_strength = int(65535 * strength / 100)
        dev.write(ecodes.EV_FF, ecodes.FF_AUTOCENTER, autocenter_strength)
        logging.debug("Setting autocenter strength: " + str(autocenter_strength))

    def set_ff_gain(self, device_id, gain):
        dev = InputDevice(self.devices[device_id]['devName'])
        ff_gain = int(65535 * gain / 100)
        dev.write(ecodes.EV_FF, ecodes.FF_GAIN, ff_gain)
        logging.debug("Setting FF gain: " + str(ff_gain))

    def is_read_only(self, device_id):
        if not self.check_file_permissions(self.device_file(device_id, 'alternate_modes')):
            return True
        if not self.check_file_permissions(self.device_file(device_id, 'range')):
            return True
        if not self.check_file_permissions(self.device_file(device_id, 'combine_pedals')):
            return True
        return False

    def check_file_permissions(self, path):
        if not os.path.isfile(path):
            return True
        if not os.access(path, os.F_OK):
            return True
        if os.access(path, os.W_OK):
            return True
        return False

