from .signal import Signal

class LinearChart:

    def __init__(self, input_values, output_values, wheelrange):
        self.input = Signal(input_values, periods = True, resample=True)
        self.output = Signal(output_values, resample = True)

        self.fposdata = self.output.filter(5)

        self.veldata = self.fposdata.derive(wheelrange / 2 * 60 / 360)
        self.fveldata = self.veldata.filter(10)

        self.fixed_input = Signal([(t, abs(v)) for t, v in self.input.get_values()])
        self.linearity = Signal(self.normalize(self.input.get_values(), [(t, abs(v)) for t, v in self.fveldata.get_values()]))

        linearity_values = [(0, 0)]
        periods = self.input.get_periods()
        t0, _ = periods[1]
        for t1, _ in periods[2:]:
            v = self.get_max_velocity(t0, t1)
            linearity_values.append((t1, v))
            t0 = t1

        self.linearity = Signal(self.normalize(self.input.get_values(), linearity_values))

    def normalize(self, signal, output):
        max_input = max([abs(v[1]) for v in signal])
        max_output = max([abs(v[1]) for v in output])
        return [(v[0], v[1] * max_input / max_output) for v in output]

    def get_max_velocity(self, t1, t2):
        if t1 >= t2:
            return 0
        return max([abs(v[1]) for v in self.fveldata.slice(t1, t2)])

    def get_input_values(self):
        return self.input.get_values()

    def get_output_values(self):
        return self.output.get_values()

    def get_fixed_input_values(self):
        return self.fixed_input.get_values()

    def get_linearity_values(self):
        return self.linearity.get_values()

    def set_minimum_level(self, minimum_level):
        self.minimum_level = float(minimum_level)

    def get_minimum_level(self):
        return self.minimum_level

    def get_minimum_level_percent(self):
        return self.minimum_level * 100 / 0x7fff
