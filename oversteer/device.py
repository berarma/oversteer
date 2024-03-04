from evdev import ecodes, InputDevice
import grp
import logging
import os
import pwd
import re
import select
import time
from . import wheel_ids as wid

logging.basicConfig(level=logging.DEBUG)

class Device:

    last_axis_value = {
        ecodes.ABS_X: 0,
        ecodes.ABS_Y: 0,
        ecodes.ABS_Z: 0,
        ecodes.ABS_RZ: 0,
    }

    def __init__(self, device_manager, data):
        self.device_manager = device_manager
        self.input_device = None
        self.id = None
        self.vendor_id = None
        self.product_id = None
        self.usb_id = None
        self.dev_path = None
        self.dev_name = None
        self.name = None
        self.ready = True
        self.max_range = None

        self.set(data)

    def set(self, data):
        for key, value in data.items():
            setattr(self, key, value)

    def close(self):
        if self.input_device is not None:
            self.input_device.close()
            self.input_device = None

    def disable(self):
        self.dev_name = None
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

    def get_max_range(self):
        return self.max_range

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
        while not self.is_ready():
            time.sleep(1)
        # Wait a bit more
        time.sleep(5)
        return True

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
                    event = self.normalize_event(event)
                    if event.type == ecodes.EV_ABS:
                        self.last_axis_value[ecodes.ABS_X] = event.value
                    yield event

    def normalize_event(self, event):
        #
        # Oversteer expects axes as follows:
        #
        # - Steering wheel direction: ABS_X [0, 65535]
        # - Throttle: ABS_Z [0, 255]
        # - Brakes: ABS_RZ [0, 255]
        # - Clutch: ABS_Y [0, 255]
        # - Hat X: ABS_HAT0X [-1, 1]
        # - Hat Y: ABS_HAT0Y [-1, 1]
        #
        if event.type != ecodes.EV_ABS:
            return event

        if event.code == ecodes.ABS_X:
            if self.usb_id in [wid.LG_WFG, wid.LG_WFFG]:
                event.value = event.value * 64
            elif self.usb_id in [wid.LG_SFW, wid.LG_MOMO, wid.LG_MOMO2, wid.LG_DF, wid.LG_DFP, wid.LG_DFGT, wid.LG_G25, wid.LG_G27]:
                event.value = event.value * 4
            elif self.vendor_id == wid.VENDOR_CAMMUS:
                event.value = event.value + 32768
        elif self.usb_id in [wid.LG_WFG, wid.LG_WFFG, wid.LG_SFW, wid.LG_MOMO, wid.LG_MOMO2, wid.LG_DF, wid.LG_DFP,
                wid.LG_DFGT, wid.LG_G920]:
            if event.code == ecodes.ABS_Y:
                event.code = ecodes.ABS_Z
            elif event.code == ecodes.ABS_Z:
                event.code = ecodes.ABS_RZ
            elif event.code == ecodes.ABS_RZ:
                event.code = ecodes.ABS_Y
        elif self.usb_id in [wid.TM_T248, wid.TM_T150, wid.TM_TMX]:
            if event.code == ecodes.ABS_RZ:
                event.code = ecodes.ABS_Z
            elif event.code == ecodes.ABS_Y:
                event.code = ecodes.ABS_RZ
            elif event.code == ecodes.ABS_THROTTLE:
                event.code = ecodes.ABS_Y
        elif self.vendor_id == wid.VENDOR_FANATEC and event.code in [ecodes.ABS_Y, ecodes.ABS_Z, ecodes.ABS_RZ]:
            event.value = int(event.value + 32768 / 257)
        elif self.usb_id == wid.LG_GPRO:
            if event.code in [ecodes.ABS_RX, ecodes.ABS_RY, ecodes.ABS_RZ]:
                event.value = int(255 - event.value / 257)
                if event.code == ecodes.ABS_RX:
                    event.code = ecodes.ABS_Z
                elif event.code == ecodes.ABS_RY:
                    event.code = ecodes.ABS_RZ
                elif event.code == ecodes.ABS_RZ:
                    event.code = ecodes.ABS_Y
        elif self.usb_id == wid.LG_G923X:
            if event.code == ecodes.ABS_Y:
                event.code = ecodes.ABS_Z
            elif event.code == ecodes.ABS_RZ:
                event.code = ecodes.ABS_Y
            elif event.code == ecodes.ABS_Z:
                event.code = ecodes.ABS_RZ

        return event
