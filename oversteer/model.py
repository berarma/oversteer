class Model:

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
        'overlay_window_pos': (20, 20),
        'use_buttons': None,
    }

    def __init__(self, device, ui = None):
        self.device = device
        self.ui = ui
        self.data = self.defaults.copy()
        self.reference_values = None
        if device is not None:
            self.read_device_settings()

    def read_device_settings(self):
        self.data.update({
            'mode': self.device.get_mode(),
            'range': self.device.get_range(),
            'ff_gain': self.device.get_ff_gain() * 100 / 65535,
            'autocenter': self.device.get_autocenter() * 100 * 65535,
            'combine_pedals': self.device.get_combine_pedals(),
            'spring_level': self.device.get_spring_level(),
            'damper_level': self.device.get_damper_level(),
            'friction_level': self.device.get_friction_level(),
            'ffb_leds': self.device.get_ffb_leds(),
            'ffb_overlay': False if self.device.get_peak_ffb_level() is not None else None,
            'range_overlay': False if self.device.get_peak_ffb_level() is not None else None,
            'use_buttons': False if self.device.get_range() is not None else None,
        })
        # Some settings are read incorrectly sometimes
        self.flush_device()

    def load_settings(self, data):
        data = dict(self.defaults, **data)
        if data['mode'] is not None:
            self.set_mode(data['mode'])
        if self.ui is not None:
            self.flush_ui(data)
        else:
            self.flush_device(data)

    def flush_device(self, data = None):
        if data is None:
            data = self.data
        self.set_range(data['range'])
        self.set_combine_pedals(data['combine_pedals'])
        self.set_autocenter(data['autocenter'])
        self.set_ff_gain(data['ff_gain'])
        self.set_spring_level(data['spring_level'])
        self.set_damper_level(data['damper_level'])
        self.set_friction_level(data['friction_level'])
        self.set_ffb_leds(data['ffb_leds'])
        self.set_ffb_overlay(data['ffb_overlay'])
        self.set_range_overlay(data['range_overlay'])
        self.set_overlay_window_pos(data['overlay_window_pos'])
        self.set_use_buttons(data['use_buttons'])

    def flush_ui(self, data = None):
        if data is None:
            data = self.data
        self.ui.set_mode(data['mode'])
        self.ui_set_range(data['range'])
        self.ui_set_combine_pedals(data['combine_pedals'])
        self.ui_set_autocenter(data['autocenter'])
        self.ui_set_ff_gain(data['ff_gain'])
        self.ui_set_spring_level(data['spring_level'])
        self.ui_set_damper_level(data['damper_level'])
        self.ui_set_friction_level(data['friction_level'])
        self.ui_set_ffb_leds(data['ffb_leds'])
        self.ui_set_ffb_overlay(data['ffb_overlay'])
        self.ui_set_range_overlay(data['range_overlay'])
        self.ui_set_overlay_window_pos(data['overlay_window_pos'])
        self.ui_set_use_buttons(data['use_buttons'])

    def to_dict(self):
        return self.data.copy()

    def save_reference_values(self):
        self.reference_values = self.data.copy()
        self.ui.disable_save_profile()

    def clear_reference_values(self):
        self.reference_values = None
        self.ui.disable_save_profile()

    def get_mode_list(self):
        return self.device.list_modes()

    def set_if_changed(self, key, value):
        if self.data[key] != value:
            self.data[key] = value
            if self.ui is not None:
                if self.reference_values is not None:
                    self.ui.disable_save_profile()
                    for k, v in self.data.items():
                        if self.reference_values[k] != v:
                            self.ui.enable_save_profile()
                            break
            return True
        return False

    def set_mode(self, value):
        if self.set_if_changed('mode', value):
            self.device.set_mode(value)
            self.read_device_settings()
            if self.ui is not None:
                self.flush_ui()

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
            self.device.set_ff_gain(value * 65535 / 100)

    def get_ff_gain(self):
        return self.data['ff_gain']

    def set_autocenter(self, value):
        value = int(value)
        if self.set_if_changed('autocenter', value):
            self.device.set_autocenter(value * 65535 / 100)

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

    def set_overlay_window_pos(self, value):
        self.set_if_changed('overlay_window_pos', value)

    def get_overlay_window_pos(self):
        return self.data['overlay_window_pos']

    def set_use_buttons(self, value):
        self.set_if_changed('use_buttons', bool(value))

    def get_use_buttons(self):
        return self.data['use_buttons']

    def ui_set_mode(self, value):
        self.ui.set_mode(value)

    def ui_set_range(self, value):
        self.ui.set_range(value)

    def ui_set_ff_gain(self, value):
        self.ui.set_ff_gain(value)

    def ui_set_autocenter(self, value):
        self.ui.set_autocenter(value)

    def ui_set_combine_pedals(self, value):
        self.ui.set_combine_pedals(value)

    def ui_set_spring_level(self, value):
        self.ui.set_spring_level(value)

    def ui_set_damper_level(self, value):
        self.ui.set_damper_level(value)

    def ui_set_friction_level(self, value):
        self.ui.set_friction_level(value)

    def ui_set_ffb_leds(self, value):
        self.ui.set_ffb_leds(value)

    def ui_set_ffb_overlay(self, value):
        self.ui.set_ffb_overlay(value)

    def ui_set_range_overlay(self, value):
        self.ui.set_range_overlay(value)

    def ui_set_overlay_window_pos(self, value):
        self.ui.set_overlay_window_pos(value)

    def ui_set_use_buttons(self, value):
        self.ui.set_use_buttons(value)
