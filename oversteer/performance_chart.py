import numpy as np
from .signal import Signal

class PerformanceChart:

    def __init__(self, input_values, output_values, wheelrange):
        self.input = Signal(input_values, periods = True, resample=True)
        self.posdata = Signal(output_values, resample = True)

        self.fposdata = self.posdata.filter(20)

        self.veldata = self.fposdata.derive(wheelrange / 2 * 60 / 360)
        self.fveldata = self.veldata.filter(15)

        self.acceldata = self.fveldata.derive()
        self.facceldata = self.acceldata.filter(15)

    def get_input_values(self):
        return self.input.get_values()

    def get_pos_values(self):
        return self.posdata.get_values()

    def get_filtered_pos_values(self):
        return self.fposdata.get_values()

    def get_velocity_values(self):
        return self.veldata.get_values()

    def get_filtered_velocity_values(self):
        return self.fveldata.get_values()

    def get_accel_values(self):
        return self.acceldata.get_values()

    def get_filtered_accel_values(self):
        return self.facceldata.get_values()

    def get_latency(self):
        noiselevel = self.posdata.noise_level(*self.input.get_range(0, 1))
        posdata = self.posdata.slice(*self.input.get_range(1, 2))
        v0 = posdata[0][1]
        for t, v in posdata:
            if abs(v - v0) > noiselevel:
                return t - self.input.get_period_start(1)

    def get_max_velocity(self):
        return max([abs(v[1]) for v in self.fveldata.slice(*self.input.get_range(1, 2))])

    def get_time_to_max_velocity(self):
        return max(self.fveldata.slice(*self.input.get_range(1, 2)), key = lambda i : abs(i[1]))[0]

    def get_max_accel(self):
        return max([abs(v[1]) for v in self.facceldata.slice(*self.input.get_range(1, 2))])

    def get_time_to_max_accel(self):
        return max(self.facceldata.slice(*self.input.get_range(1, 2)), key = lambda i : abs(i[1]))[0] - self.input.get_period_start(1)

    def get_max_decel(self):
        t1 = self.input.get_period_start(2)
        t2 = self.fveldata.xzero_time(*self.input.get_range(2, 3))
        if t1 >= t2:
            return 0
        return max([abs(v[1]) for v in self.facceldata.slice(t1, t2)])

    def get_time_to_max_decel(self):
        t1 = self.input.get_period_start(2)
        t2 = self.fveldata.xzero_time(*self.input.get_range(2, 3))
        if t1 >= t2:
            return 0
        return max(self.facceldata.slice(t1, t2), key = lambda i : abs(i[1]))[0] - t1

    def get_mean_accel(self):
        max_velocity = self.get_max_velocity()
        for t, v in self.fveldata.slice(*self.input.get_range(1, 2)):
            if abs(v) >= max_velocity:
                return abs(v) / (t - self.get_latency())

    def get_mean_decel(self):
        t1 = self.input.get_period_start(2)
        t2 = self.fveldata.xzero_time(*self.input.get_range(2, 3))
        if t1 >= t2:
            return 0
        return self.get_max_velocity() / (t2 - t1)

    def get_residual_decel(self):
        t1 = self.input.get_period_start(4)
        t2 = self.fveldata.xzero_time(*self.input.get_range(4, 5))
        if t2 is None:
            t2 = self.input.get_period_start(5)
        t2 = min(t1 + 0.2, t2)
        return abs(np.mean([v[1] for v in self.facceldata.slice(t1, t2)]))

    def get_estimated_snr(self):
        return self.posdata.estimated_snr(self.fposdata)
