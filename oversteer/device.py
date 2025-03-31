from evdev import ecodes, InputDevice
import grp
import logging
import os
import pwd
import re
import select
import time
from .device_event import DeviceEvent

logging.basicConfig(level=logging.DEBUG)

class Device:

    def __init__(self, device_manager, data):
        self.last_axis_value = {
            ecodes.ABS_X: 0,
            ecodes.ABS_Y: 0,
            ecodes.ABS_Z: 0,
            ecodes.ABS_RZ: 0,
        }
        self.device_manager = device_manager
        self.input_device = None
        self.id = ""
        self.vendor_id = ""
        self.product_id = ""
        self.usb_id = ""
        self.dev_path = ""
        self.dev_name = ""
        self.name = ""
        self.ready = True
        self.rotation = 0
        self.input_map = [] 

        self.set(data)

    def set(self, data):
        for key, value in data.items():
            setattr(self, key, value)

    def close(self):
        if self.input_device is not None:
            self.input_device.close()
            self.input_device = None

    def disable(self):
        self.ready = False
        self.close()

    def enable(self):
        self.ready = True

    def is_ready(self):
        return self.ready

    def get_id(self):
        return self.id

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
        status = os.stat(path)
        logging.debug("check_file_permissions mode: %s user: %s group: %s file: %s", oct(status.st_mode & 0o777),
                pwd.getpwuid(status.st_uid)[0], grp.getgrgid(status.st_gid)[0], path)
        if os.access(path, os.R_OK | os.W_OK):
            return True
        return False

    def get_rotation(self):
        return self.rotation

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

        mode_id = None
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
        self.disable()
        logging.debug("Setting mode: %s", str(emulation_mode))
        with open(path, "w") as file:
            file.write(emulation_mode)
        # Wait for device ready
        for i in range(10):
            if self.is_ready():
                return True
            time.sleep(1)
        return False

    def get_range(self):
        path = self.checked_device_file("range")
        if not path:
            return None
        with open(path, "r") as file:
            data = file.read()
        wrange = data.strip()
        return int(wrange)

    def set_range(self, wrange):
        path = self.checked_device_file("range")
        if not path:
            return False
        wrange = str(wrange)
        logging.debug("Setting range: %s", wrange)
        with open(path, "w") as file:
            file.write(wrange)
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
        logging.debug("Setting combined pedals: %s", combine_pedals)
        with open(path, "w") as file:
            file.write(combine_pedals)
        return True

    def get_autocenter(self):
        path = self.checked_device_file("autocenter")
        if not path:
            capabilities = self.get_capabilities()
            if ecodes.EV_FF in capabilities and ecodes.FF_AUTOCENTER in capabilities[ecodes.EV_FF]:
                return 0
            else:
                return None
        with open(path, "r") as file:
            data = file.read()
        autocenter = data.strip()
        return int(round((int(autocenter) * 100) / 65535))

    def set_autocenter(self, autocenter):
        if autocenter > 100:
            autocenter = 100
        autocenter = str(int(autocenter / 100.0 * 65535))
        logging.debug("Setting autocenter strength: %s", autocenter)
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
            capabilities = self.get_capabilities()
            if ecodes.EV_FF in capabilities and ecodes.FF_GAIN in capabilities[ecodes.EV_FF]:
                return 100
            else:
                return None
        with open(path, "r") as file:
            data = file.read()
        gain = int(data.strip())
        return int(round((int(gain) * 100) / 65535))

    def set_ff_gain(self, gain):
        if gain > 100:
            gain = 100
        gain = str(int(gain / 100.0 * 65535))
        logging.debug("Setting FF gain: %s", gain)
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
        logging.debug("Setting spring level: %s", level)
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
        logging.debug("Setting damper level: %s", level)
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
        logging.debug("Setting friction level: %s", level)
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
        logging.debug("Setting FF leds: %s", ffb_leds)
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
        logging.debug("Setting peak FF level: %s", peak_ffb_level)
        with open(path, "w") as file:
            file.write(peak_ffb_level)
        return True

    def center_wheel(self):
        self.set_autocenter(100)
        time.sleep(1)
        self.set_autocenter(0)

    def check_permissions(self):
        logging.debug("check_permissions: %s", self.dev_path)
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

    def get_last_axis_value(self, axis):
        return self.last_axis_value[axis]

    def get_input_device(self):
        if self.input_device is None or self.input_device.fd == -1:
            if os.access(self.dev_name, os.R_OK):
                self.input_device = InputDevice(self.dev_name)
        return self.input_device

    def get_capabilities(self):
        return self.get_input_device().capabilities()

    def read_events(self, timeout):
        input_device = self.get_input_device()
        if input_device is not None and input_device.fd != -1:
            r, _, _ = select.select({input_device.fd: input_device}, [], [], timeout)
            if input_device.fd in r:
                for event in input_device.read():
                    if event.type in self.input_map and event.code in self.input_map[event.type]:
                        device_event = DeviceEvent(self.input_map[event.type][event.code], event.value)
                        if event.type == ecodes.EV_ABS:
                            self.last_axis_value[ecodes.ABS_X] = event.value
                        yield device_event

