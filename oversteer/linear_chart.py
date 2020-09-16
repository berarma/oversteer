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

        self.final_input_values = [(0, 0)]
        self.final_accel_values = [(0, 0)]
        self.final_velocity_values = [(0, 0)]
        itr = iter(self.input.get_all_periods()[2:])
        for t1, t2 in zip(itr, itr):
            a = self.get_accel(t1, t2)

            #a = self.get_accel(self.fveldata.xzero_time(t1, t2), t2)

            v = self.get_max_velocity(t1, t2)
            input_value = abs(self.input.get_value(t1)[1])
            self.final_input_values.append((input_value, input_value))
            self.final_accel_values.append((input_value, a))
            self.final_velocity_values.append((input_value, v))

        self.final_accel_values = self.normalize(self.final_input_values, self.final_accel_values)
        self.final_velocity_values = self.normalize(self.final_input_values, self.final_velocity_values)

        self.final_accel_values = Signal(self.final_accel_values).filter(10).get_values()
        self.final_velocity_values = Signal(self.final_velocity_values).filter(10).get_values()

    def normalize(self, input, output):
        max_input = max([abs(v[1]) for v in input])
        max_output = max([abs(v[1]) for v in output])
        return [(v[0], v[1] * max_input / max_output) for v in output]

    def get_accel(self, t1, t2):
        if t1 is None:
            return 0
        ti, vi = self.fveldata.get_value(t1)
        vi *= 0.9
        ti, vi = self.fveldata.xzero(t1, t2, -vi)
        if ti is None:
            return 0
        fvelvalues = self.fveldata.slice(ti, t2)
        index = np.searchsorted([-v[1] for v in fvelvalues], vi)
        #index = np.argmax(fvelvalues)
        if index >= len(fvelvalues):
            tf, vf = fvelvalues[len(fvelvalues) - 1]
        else:
            tf, vf = fvelvalues[index]
        if tf <= ti:
            return 0
        return abs(vf - vi) / (tf - ti)

    def get_max_velocity(self, t1, t2):
        return max([abs(v[1]) for v in self.fveldata.slice(t1, t2)])

    def get_max_accel(self, t1, t2):
        return max([abs(v[1]) for v in self.facceldata.slice(t1, t2)])

    def get_input_values(self):
        return self.input.get_values()

    def get_output_values(self):
        return self.output.get_values()

    def get_filtered_velocity_values(self):
        return self.fveldata.get_values()

    def get_filtered_accel_values(self):
        return self.facceldata.get_values()

    def get_final_input_values(self):
        return self.final_input_values

    def get_final_accel_values(self):
        return self.final_accel_values

    def get_final_velocity_values(self):
        return self.final_velocity_values

    def set_minimum_level(self, minimum_level):
        self.minimum_level = float(minimum_level)

    def get_minimum_level(self):
        return self.minimum_level

    def get_minimum_level_percent(self):
        return self.minimum_level * 100 / 0x7fff
