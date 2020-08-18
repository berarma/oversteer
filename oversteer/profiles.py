import configparser

class Profile:

    def __init__(self, data = None):
        self.config = configparser.ConfigParser()
        if data is not None:
            self.import_settings(data)

    def load(self, profile_file):
        self.config = configparser.ConfigParser()
        self.config.read(profile_file)

    def save(self, profile_file):
        with open(profile_file, 'w') as configfile:
            self.config.write(configfile)

    def export_settings(self):
        return self.config['DEFAULT']

    def import_settings(self, data):
        self.config['DEFAULT'] = {**self.config['DEFAULT'], **data}

    def set_mode(self, mode):
        self.set('mode', mode)

    def set_range(self, range):
        self.set('range', int(range))

    def set_combine_pedals(self, combine_pedals):
        self.set('combine_pedals', int(combine_pedals))

    def set_autocenter(self, autocenter):
        self.set('autocenter', int(autocenter))

    def set_ff_gain(self, ff_gain):
        self.set('ff_gain', int(ff_gain))

    def set_spring_level(self, level):
        self.set('spring_level', int(level))

    def set_damper_level(self, level):
        self.set('damper_level', int(level))

    def set_friction_level(self, level):
        self.set('friction_level', int(level))

    def set_ffbmeter_leds(self, state):
        self.set('ffbmeter_leds', int(state))

    def set_ffbmeter_overlay(self, state):
        self.set('ffbmeter_overlay', int(state))

    def set_wheel_range_overlay(self, id):
        self.set('wheel_range_overlay', id)

    def set_wheel_buttons(self, state):
        self.set('wheel_buttons', int(state))

    def get_mode(self):
        return self.get('mode')

    def get_range(self):
        return self.get_int('range')

    def get_combine_pedals(self):
        combine_pedals = self.get('combine_pedals')
        if combine_pedals != None:
            if combine_pedals == 'True':
                combine_pedals = 1
            elif combine_pedals == 'False':
                combine_pedals = 0
            else:
                combine_pedals = int(combine_pedals)
        return combine_pedals

    def get_autocenter(self):
        return self.get_int('autocenter')

    def get_ff_gain(self):
        return self.get_int('ff_gain')

    def get_spring_level(self):
        return self.get_int('spring_level')

    def get_damper_level(self):
        return self.get_int('damper_level')

    def get_friction_level(self):
        return self.get_int('friction_level')

    def get_ffbmeter_leds(self):
        return self.get_int('ffbmeter_leds')

    def get_ffbmeter_overlay(self):
        return self.get_int('ffbmeter_overlay')

    def get_wheel_range_overlay(self):
        return self.get('wheel_range_overlay')

    def get_wheel_buttons(self):
        return self.get_int('wheel_buttons')

    def set(self, name, value):
        if value == None:
            return
        self.config.set('DEFAULT', name, str(value))

    def get(self, name):
        if not self.config.has_option('DEFAULT', name):
            return None
        return self.config.get('DEFAULT', name)

    def get_int(self, name):
        if not self.config.has_option('DEFAULT', name):
            return None
        return int(self.config.get('DEFAULT', name))
