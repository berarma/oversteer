from enum import Enum
from evdev import ecodes, InputDevice
import functools
import glob
import logging
import os
import pyudev
import re
import select
import time

logging.basicConfig(level=logging.DEBUG)

class Device:

    def __init__(self, device_manager, data):
        self.device_manager = device_manager
        self.input_device = None
        self.seat_id = None
        self.vendor_id = None
        self.product_id = None
        self.usb_id = None
        self.dev_path = None
        self.dev_name = None
        self.name = None
        self.ready = True

        self.set(data)

    def set(self, data):
        for key, value in data.items():
            setattr(self, key, value)

    def close(self):
        if self.input_device is not None:
            self.input_device.close()
            self.input_device = None

    def disconnect(self):
        self.ready = False
        self.close()

    def reconnect(self):
        self.ready = True

    def is_ready(self):
        return self.ready

    def get_id(self):
        return self.seat_id

    def device_file(self, filename):
        return os.path.join(self.dev_path, filename)

    def checked_device_file(self, filename):
        path = self.device_file(filename)
        if not os.access(path, os.F_OK | os.R_OK | os.W_OK):
            return False
        return path

    def check_file_permissions(self, filename):
        if filename is None:
            return True
        path = self.device_file(filename)
        if not os.access(path, os.F_OK):
            return True
        if os.access(path, os.R_OK | os.W_OK):
            return True
        return False

    def list_modes(self):
        path = self.checked_device_file("alternate_modes")
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

    def get_mode(self):
        path = self.checked_device_file("alternate_modes")
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

    def set_mode(self, emulation_mode):
        path = self.checked_device_file("alternate_modes")
        if not path:
            return False
        old_mode = self.get_mode()
        if old_mode == emulation_mode:
            return True
        self.disconnect()
        logging.debug("Setting mode: " + str(emulation_mode))
        product_id = self.product_id
        with open(path, "w") as file:
            file.write(emulation_mode)
        # Wait for device ready
        while not self.is_ready():
            time.sleep(1)
        return True

    def get_range(self):
        path = self.checked_device_file("range")
        if not path:
            return None
        with open(path, "r") as file:
            data = file.read()
        range = data.strip()
        return int(range)

    def set_range(self, range):
        path = self.checked_device_file("range")
        if not path:
            return False
        range = str(range)
        logging.debug("Setting range: " + range)
        with open(path, "w") as file:
            file.write(range)
        return True

    def get_combine_pedals(self):
        path = self.checked_device_file("combine_pedals")
        if not path:
            return None
        with open(path, "r") as file:
            data = file.read()
        combine_pedals = data.strip()
        return int(combine_pedals)

    def set_combine_pedals(self, combine_pedals):
        path = self.checked_device_file("combine_pedals")
        if not path:
            return False
        combine_pedals = str(combine_pedals)
        logging.debug("Setting combined pedals: " + combine_pedals)
        with open(path, "w") as file:
            file.write(combine_pedals)
        return True

    def get_autocenter(self):
        path = self.checked_device_file("autocenter")
        if not path:
            return 0
        with open(path, "r") as file:
            data = file.read()
        autocenter = data.strip()
        return int(autocenter)

    def set_autocenter(self, autocenter):
        autocenter = str(int(65535 * autocenter / 100))
        logging.debug("Setting autocenter strength: " + autocenter)
        path = self.checked_device_file("autocenter")
        if path:
            with open(path, "w") as file:
                file.write(autocenter)
        else:
            input_device = self.get_input_device()
            input_device.write(ecodes.EV_FF, ecodes.FF_AUTOCENTER, int(autocenter))
        return True

    def get_ff_gain(self):
        path = self.checked_device_file("gain")
        if not path:
            return 100
        with open(path, "r") as file:
            data = file.read()
        gain = int(data.strip())
        return int(gain/65530*100)

    def set_ff_gain(self, gain):
        gain = str(int(65535 * gain / 100))
        logging.debug("Setting FF gain: " + gain)
        path = self.checked_device_file("gain")
        if path:
            with open(path, "w") as file:
                file.write(gain)
        else:
            input_device = self.get_input_device()
            input_device.write(ecodes.EV_FF, ecodes.FF_GAIN, int(gain))

    def get_spring_level(self):
        path = self.checked_device_file("spring_level")
        if not path:
            return None
        with open(path, "r") as file:
            data = file.read()
        spring_level = data.strip()
        return int(spring_level)

    def set_spring_level(self, level):
        path = self.checked_device_file("spring_level")
        if not path:
            return False
        level = str(level)
        logging.debug("Setting spring level: " + level)
        with open(path, "w") as file:
            file.write(level)
        return True

    def get_damper_level(self):
        path = self.checked_device_file("damper_level")
        if not path:
            return None
        with open(path, "r") as file:
            data = file.read()
        damper_level = data.strip()
        return int(damper_level)

    def set_damper_level(self, level):
        path = self.checked_device_file("damper_level")
        if not path:
            return False
        level = str(level)
        logging.debug("Setting damper level: " + level)
        with open(path, "w") as file:
            file.write(level)
        return True

    def get_friction_level(self):
        path = self.checked_device_file("friction_level")
        if not path:
            return None
        with open(path, "r") as file:
            data = file.read()
        friction_level = data.strip()
        return int(friction_level)

    def set_friction_level(self, level):
        path = self.checked_device_file("friction_level")
        if not path:
            return False
        level = str(level)
        logging.debug("Setting friction level: " + level)
        with open(path, "w") as file:
            file.write(level)
        return True

    def get_ffb_leds(self):
        path = self.checked_device_file("ffb_leds")
        if not path:
            return None
        with open(path, "r") as file:
            data = file.read()
        ffb_leds = data.strip()
        return int(ffb_leds)

    def set_ffb_leds(self, ffb_leds):
        path = self.checked_device_file("ffb_leds")
        if not path:
            return False
        ffb_leds = str(ffb_leds)
        logging.debug("Setting FF leds: " + ffb_leds)
        with open(path, "w") as file:
            file.write(ffb_leds)
        return True

    def get_peak_ffb_level(self):
        path = self.checked_device_file("peak_ffb_level")
        if not path:
            return None
        with open(path, "r") as file:
            data = file.read()
        peak_ffb_level = data.strip()
        return int(peak_ffb_level)

    def set_peak_ffb_level(self, peak_ffb_level):
        path = self.checked_device_file("peak_ffb_level")
        if not path:
            return False
        peak_ffb_level = str(peak_ffb_level)
        logging.debug("Setting peak FF level: " + peak_ffb_level)
        with open(path, "w") as file:
            file.write(peak_ffb_level)
        return True

    def load_settings(self, settings):
        if 'mode' in settings:
            self.set_mode(settings['mode'])
        if 'range' in settings:
            self.set_range(settings['range'])
        if 'combine_pedals' in settings:
            self.set_combine_pedals(settings['combine_pedals'])
        if 'ff_gain' in settings:
            self.set_ff_gain(settings['ff_gain'])
        if 'autocenter' in settings:
            self.set_autocenter(settings['autocenter'])
        if 'spring_level' in settings:
            self.set_spring_level(settings['spring_level'])
        if 'damper_level' in settings:
            self.set_damper_level(settings['damper_level'])
        if 'friction_level' in settings:
            self.set_friction_level(settings['friction_level'])
        if 'ffb_leds' in settings:
            self.set_ffb_leds(settings['ffb_leds'])

    def save_settings(self):
        return {
            'mode': self.get_mode(),
            'range': self.get_range(),
            'combine_pedals': self.get_combine_pedals(),
            'ff_gain': self.get_ff_gain(),
            'autocenter': self.get_autocenter(),
            'spring_level': self.get_spring_level(),
            'damper_level': self.get_damper_level(),
            'friction_level': self.get_friction_level(),
            'ffb_leds': self.get_ffb_leds(),
        }

    def check_permissions(self):
        if not os.access(self.dev_path, os.F_OK | os.R_OK | os.X_OK):
            return False
        if not self.check_file_permissions('alternate_modes'):
            return False
        if not self.check_file_permissions('range'):
            return False
        if not self.check_file_permissions('combine_pedals'):
            return False
        if not self.check_file_permissions('gain'):
            return False
        if not self.check_file_permissions('autocenter'):
            return False
        if not self.check_file_permissions('spring_level'):
            return False
        if not self.check_file_permissions('damper_level'):
            return False
        if not self.check_file_permissions('friction_level'):
            return False
        if not self.check_file_permissions('ffb_leds'):
            return False
        if not self.check_file_permissions('peak_ffb_level'):
            return False
        return True

    def get_input_device(self):
        if self.input_device is None or self.input_device.fd == -1:
            if os.access(self.dev_name, os.R_OK):
                self.input_device = InputDevice(self.dev_name)
        return self.input_device

    def read_events(self, timeout):
        input_device = self.get_input_device()
        if input_device.fd == -1:
            return None
        r, w, x = select.select({input_device.fd: input_device}, [], [], timeout)
        if input_device.fd in r:
            for event in input_device.read():
                yield self.normalize_event(event)

    def normalize_event(self, event):
        if event.type == ecodes.EV_ABS:
            if event.code == ecodes.ABS_X:
                if self.usb_id not in [self.device_manager.LG_G29, self.device_manager.TM_T300RS]:
                    event.value = event.value * 4
            elif self.usb_id not in [self.device_manager.LG_DFGT, self.device_manager.LG_DFP, self.device_manager.LG_G920]:
                if event.code == ecodes.ABS_Y:
                    event.code = ecodes.ABS_RZ
                elif event.code == ecodes.ABS_Z:
                    event.code = ecodes.ABS_Y
                elif event.code == ecodes.ABS_RZ:
                    event.code = ecodes.ABS_Z
        return event
