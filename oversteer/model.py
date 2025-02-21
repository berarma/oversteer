import configparser
import logging

class Model:

    profile = None
    device = None

    defaults = {
        'mode': None,
        'range': None,
        'ff_gain': None,
        'autocenter': None,
        'combine_pedals': None,
        'spring_level': None,
        'damper_level': None,
        'friction_level': None,
        'ffb_leds': None,
        'ffb_overlay': None,
        'range_overlay': None,
        'use_buttons': None,
        'center_wheel': None,
        'start_app_manually': None,
    }

    types = {
        'mode': 'string',
        'range': 'integer',
        'ff_gain': 'integer',
        'autocenter': 'integer',
        'combine_pedals': 'integer',
        'spring_level': 'integer',
        'damper_level': 'integer',
        'friction_level': 'integer',
        'ffb_leds': 'integer',
        'ffb_overlay': 'boolean',
        'range_overlay': 'string',
        'use_buttons': 'boolean',
        'center_wheel': 'boolean',
        'start_app_manually': 'boolean',
    }

    def __init__(self, device = None, ui = None):
        self.ui = ui
        self.reference_values = None
        self.data = self.defaults.copy()
        if device != None:
            self.set_device(device)

    def get_device(self):
        return self.device

    def set_device(self, device):
        self.device = device
        pending_data = self.data.copy()
        self.update_from_device_settings()
        for k, v in pending_data.items():
            if v != None:
                self.data[k] = v

    def set_ui(self, ui):
        self.ui = ui

    def update_save_profile_button(self):
        self.ui.disable_save_profile()
        if self.ui is None or self.reference_values is None:
            return
        for (key, value) in self.reference_values.items():
            if self.data[key] != value:
                self.ui.enable_save_profile()

    def read_device_settings(self):
        return {
            'mode': self.device.get_mode(),
            'range': self.device.get_range(),
            'ff_gain': self.device.get_ff_gain(),
            'autocenter': self.device.get_autocenter(),
            'combine_pedals': self.device.get_combine_pedals(),
            'spring_level': self.device.get_spring_level(),
            'damper_level': self.device.get_damper_level(),
            'friction_level': self.device.get_friction_level(),
            'ffb_leds': self.device.get_ffb_leds(),
            'ffb_overlay': False if self.device.get_peak_ffb_level() is not None else None,
            'range_overlay': 'never' if self.device.get_peak_ffb_level() is not None else None,
            'use_buttons': False if self.device.get_range() is not None else None,
            'center_wheel': False,
            'start_app_manually': False,
        }

    def update_from_device_settings(self):
        self.data.update(self.read_device_settings())

    def get_profile(self):
        return self.profile

    def load(self, profile_file):
        logging.debug('Load')

        if profile_file == self.profile:
            return

        config = configparser.ConfigParser()
        config.read(profile_file)
        data = self.defaults.copy()
        for (key, value) in config['DEFAULT'].items():
            if key not in self.types:
                logging.warning("Unknown profile setting name: %s", key)
                continue
            if value is None:
                continue
            if self.types[key] == 'string':
                data[key] = value
            elif self.types[key] == 'integer':
                data[key] = int(value)
            elif self.types[key] == 'boolean':
                data[key] = bool(int(value))
            elif self.types[key] == 'tuple':
                data[key] = tuple(map(int, value.split(',')))

        self.data = data
        self.save_reference_values()
        self.profile = profile_file

        logging.debug("\n".join('{0} = {1}'.format(k, v) for k, v in self.data.items()))

    def save(self, profile_file):
        data = {}
        for key, value in self.data.items():
            if value is None:
                continue
            if self.types[key] == 'string':
                data[key] = value
            elif self.types[key] == 'integer':
                data[key] = int(value)
            elif self.types[key] == 'boolean':
                data[key] = int(bool(value))
            elif self.types[key] == 'tuple':
                data[key] = ','.join(map(str, value))

        config = configparser.ConfigParser()
        config['DEFAULT'] = data
        with open(profile_file, 'w') as configfile:
            config.write(configfile)

        self.save_reference_values()

    def save_reference_values(self):
        data = self.data.copy()
        self.reference_values = data
        if self.ui is not None:
            self.ui.disable_save_profile()

    def set_if_changed(self, key, value):
        if self.data[key] != value:
            self.data[key] = value
            if self.ui is not None:
                self.update_save_profile_button()
            if self.device:
                return True
        return False

    def get_mode_list(self):
        return self.device.list_modes()

    def set_mode(self, value):
        if self.set_if_changed('mode', value):
            self.device.set_mode(value)

    def get_mode(self):
        return self.data['mode']

    def set_range(self, value):
        value = int(value)
        if self.set_if_changed('range', value):
            self.device.set_range(value)

    def get_range(self):
        return self.data['range']

    def set_ff_gain(self, value):
        value = int(value)
        if self.set_if_changed('ff_gain', value):
            self.device.set_ff_gain(value)

    def get_ff_gain(self):
        return self.data['ff_gain']

    def set_autocenter(self, value):
        value = int(value)
        if self.set_if_changed('autocenter', value):
            self.device.set_autocenter(value)

    def get_autocenter(self):
        return self.data['autocenter']

    def set_combine_pedals(self, value):
        value = int(value)
        if self.set_if_changed('combine_pedals', value):
            self.device.set_combine_pedals(value)

    def get_combine_pedals(self):
        return self.data['combine_pedals']

    def set_spring_level(self, value):
        value = int(value)
        if self.set_if_changed('spring_level', value):
            self.device.set_spring_level(value)

    def get_spring_level(self):
        return self.data['spring_level']

    def set_damper_level(self, value):
        value = int(value)
        if self.set_if_changed('damper_level', value):
            self.device.set_damper_level(value)

    def get_damper_level(self):
        return self.data['damper_level']

    def set_friction_level(self, value):
        value = int(value)
        if self.set_if_changed('friction_level', value):
            self.device.set_friction_level(value)

    def get_friction_level(self):
        return self.data['friction_level']

    def set_ffb_leds(self, value):
        value = bool(value)
        if self.set_if_changed('ffb_leds', value):
            self.device.set_ffb_leds(1 if value else 0)

    def get_ffb_leds(self):
        return self.data['ffb_leds']

    def set_ffb_overlay(self, value):
        self.set_if_changed('ffb_overlay', bool(value))

    def get_ffb_overlay(self):
        return self.data['ffb_overlay']

    def set_range_overlay(self, value):
        self.set_if_changed('range_overlay', value)

    def get_range_overlay(self):
        return self.data['range_overlay']

    def set_use_buttons(self, value):
        self.set_if_changed('use_buttons', bool(value))

    def get_use_buttons(self):
        return self.data['use_buttons']

    def set_center_wheel(self, value=True):
        value = bool(value)
        if self.set_if_changed('center_wheel', value):
            self.device.center_wheel(value)

    def set_start_app_manually(self, value):
        value = bool(value)
        self.set_if_changed('start_app_manually', value)

    def get_start_app_manually(self):
        return self.data['start_app_manually']

    def flush_device(self):
        logging.debug("flush_device")
        if self.data['mode'] is not None:
            self.device.set_mode(self.data['mode'])
        if self.data['range'] is not None:
            self.device.set_range(self.data['range'])
        if self.data['combine_pedals'] is not None:
            self.device.set_combine_pedals(self.data['combine_pedals'])
        if self.data['center_wheel']:
            self.device.center_wheel()
        if self.data['autocenter'] is not None:
            self.device.set_autocenter(self.data['autocenter'])
        if self.data['ff_gain'] is not None:
            self.device.set_ff_gain(self.data['ff_gain'])
        if self.data['spring_level'] is not None:
            self.device.set_spring_level(self.data['spring_level'])
        if self.data['damper_level'] is not None:
            self.device.set_damper_level(self.data['damper_level'])
        if self.data['friction_level'] is not None:
            self.device.set_friction_level(self.data['friction_level'])
        if self.data['ffb_leds'] is not None:
            self.device.set_ffb_leds(self.data['ffb_leds'])

    def flush_ui(self, data = None):
        logging.debug("flush_ui")
        if data is None:
            data = self.data
        self.ui.set_mode(data['mode'])
        self.ui.set_range(data['range'])
        self.ui.set_ff_gain(data['ff_gain'])
        self.ui.set_autocenter(data['autocenter'])
        self.ui.set_combine_pedals(data['combine_pedals'])
        self.ui.set_spring_level(data['spring_level'])
        self.ui.set_damper_level(data['damper_level'])
        self.ui.set_friction_level(data['friction_level'])
        self.ui.set_ffb_leds(data['ffb_leds'])
        self.ui.set_ffb_overlay(data['ffb_overlay'])
        self.ui.set_range_overlay(data['range_overlay'])
        self.ui.set_use_buttons(data['use_buttons'])
        self.ui.set_center_wheel(data['center_wheel'])
        self.ui.set_start_app_manually(data['start_app_manually'])
        self.update_save_profile_button()

