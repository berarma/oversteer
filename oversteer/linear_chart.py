import numpy as np
from .signal import Signal

class LinearChart:

    def __init__(self, input_values, output_values, wheelrange):
        self.input = Signal(input_values, periods = True, resample = True)
        self.output = Signal(output_values, resample = True)

        self.fposdata = self.output.filter(10)

        self.veldata = self.fposdata.derive(wheelrange / 2 * 60 / 360)
        self.fveldata = self.veldata.filter(20)

        self.acceldata = self.fveldata.derive()
        self.facceldata = self.acceldata.filter(20)

    def normalize(self, input, output):
        max_input = max([abs(v[1]) for v in input])
        max_output = max([abs(v[1]) for v in output])
        return [(v[0], v[1] * max_input / max_output) for v in output]

    def get_input_values(self):
        return self.input.get_values()

    def get_output_values(self):
        return self.output.get_values()

    def get_filtered_velocity_values(self):
        return self.normalize(self.input.get_values(), self.fveldata.get_values())

    def get_filtered_accel_values(self):
        return self.normalize(self.input.get_values(), self.facceldata.get_values())

    def set_minimum_level(self, minimum_level):
        self.minimum_level = float(minimum_level)

    def get_minimum_level(self):
        return self.minimum_level

    def get_minimum_level_percent(self):
        return self.minimum_level * 100 / 0x7fff
