import math
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import LinearLocator
from matplotlib.backends.backend_gtk3cairo import FigureCanvasGTK3Cairo as FigureCanvas
from matplotlib.backends.backend_gtk3 import NavigationToolbar2GTK3 as NavigationToolbar
from scipy.signal import savgol_filter
from scipy.ndimage.filters import uniform_filter1d

class TestChart:
    def __init__(self, input_values, pos_values):
        self.input_values = self.resample(input_values)
        self.posdata = self.resample(pos_values)

        self.fposdata = self.filter_serie(self.posdata, 10)

        self.veldata = self.derive_serie(self.fposdata, 450 * 60 / 360)
        self.fveldata = self.filter_serie(self.veldata, 20)

        self.acceldata = self.derive_serie(self.fveldata)
        self.facceldata = self.filter_serie(self.acceldata, 20)

        self.periods = [self.input_values[0][0]]
        v0 = self.input_values[0][1]
        for t, v in self.input_values:
            if v - v0 != 0:
                self.periods.append(t)
                v0 = v
        self.periods.append(t)

    def derive_serie(self, data, multiplier = 1):
        newdata = [(0, 0)]
        for t, v in data:
            if t > 0:
                newval = (v - v0) * multiplier / (t - t0)
                newdata.append((t, newval))
            t0 = t
            v0 = v

        return newdata

    def filter_serie(self, data, average_size):
        (times, values) = zip(*data)
        #times = [t / 1000 for t in range(0, average_size // 2)] + [t + average_size // 2 / 1000 for t in times]
        #values = [values[0] for v in range(0, average_size // 2)] + list(values)
        filtered_data = uniform_filter1d(values, size=average_size)
        newdata = list(zip(times, filtered_data))

        return newdata

    def get_input_values(self):
        return self.input_values

    def get_pos_values(self):
        return self.posdata

    def get_canvas(self):
        fig, (ax1, ax2, ax3) = plt.subplots(3, 1)

        ax1.title.set_text('Angular displacement')
        p1, = ax1.step(*zip(*self.input_values), label='Input force', color='blue')
        p2, = ax1.step(*zip(*self.posdata), label='Angular displacement (raw)', color='lightgray')
        p3, = ax1.plot(*zip(*self.fposdata), label='Angular displacement (smoothed)', color='gray')
        ax1.tick_params(axis='y', labelcolor='gray')
        ax1.set_ylabel('Rotation range')
        ax1.grid(True)

        ax2.title.set_text('Angular velocity')
        p4, = ax2.plot(*zip(*self.veldata), label='Angular velocity (raw)', color='lightgreen')
        p5, = ax2.plot(*zip(*self.fveldata), label='Angular velocity (smoothed)', color='green')
        input_values = [(t, v * max(self.veldata, key=lambda x:x[1])[1]) for t, v in self.input_values]
        ax2.step(*zip(*input_values), label='Input Force', color='blue')
        ax2.tick_params(axis='y', labelcolor='green')
        ax2.set_ylabel('RPM')
        ax2.grid(True)

        ax3.title.set_text('Angular acceleration')
        p6, = ax3.plot(*zip(*self.acceldata), label='Angular acceleration (raw)', color='orange')
        p7, = ax3.plot(*zip(*self.facceldata), label='Angular acceleration (smoothed)', color='red')
        input_values = [(t, v * max(self.acceldata, key=lambda x:x[1])[1]) for t, v in self.input_values]
        ax3.step(*zip(*input_values), label='Input Force', color='blue')
        ax3.set_xlabel('Time (s)')
        ax3.set_ylabel('RPM/s')
        ax3.tick_params(axis='y', labelcolor='red')
        ax3.grid(True)

        props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)
        text = [
            'Latency = {:.0f} ms',
            'Max. velocity = {:.0f} RPM',
            'Mean accel. = {:.0f} RPM/s',
            'Mean decel. = {:.0f} RPM/s',
            'Max. accel. = {:.0f} RPM/s',
            'Time max. accel. = {:.0f} ms',
            'Max. decel. = {:.0f} RPM/s',
            'Time max. decel. = {:.0f} ms',
            'Residual decel. = {:.0f} ms',
            'Estimated SNR = {:.0f} dB',
        ]
        values = [
            self.latency() * 1000,
            self.max_velocity(),
            self.mean_accel(),
            self.mean_decel(),
            self.max_accel(),
            self.time_to_max_accel() * 1000,
            self.max_decel(),
            self.time_to_max_decel() * 1000,
            self.residual_decel(),
            self.estimated_snr(),
        ]
        ax1.text(1.02, 0.95, '\n'.join(text).format(*values), transform=ax1.transAxes, fontsize=10, verticalalignment='top', bbox=props)
        fig.subplots_adjust(left=0.1, right=0.8)

        subplots = [p2, p3, p4, p5, p6, p7, p1]
        plt.figlegend(subplots, [p.get_label() for p in subplots], loc='upper center', mode=None, ncol=4)

        canvas = FigureCanvas(fig)

        return canvas

    def get_navigation_toolbar(self, canvas, window):
        return NavigationToolbar(canvas, window)

    def resample(self, data):
        newdata = []
        new_t = 0
        for t, v in data:
            if t > 0:
                new_t = math.ceil(t * 1000) / 1000
                if new_t > t0:
                    length = round(new_t * 1000) - round(t0 * 1000)
                    for delta_time in range(0, length):
                        newdata.append((t0 + delta_time / 1000, v0))
            t0 = new_t
            v0 = v

        return newdata

    def slice(self, data, t1, t2):
        return [v for v in data if t1 <= v[0] < t2]

    def slice_range(self, data, i1, i2):
        return self.slice(data, self.periods[i1], self.periods[i2])

    def noise_level(self):
        minv = 1
        maxv = -1
        sumv = 0
        count = 0
        for _, v in self.slice_range(self.posdata, 0, 1):
            sumv += v
            if v < minv:
                minv = v
            if v > maxv:
                maxv = v
            count += 1
        mean = sumv / count

        return max(mean - minv, maxv - mean)

    def xzero_time(self, data):
        v0 = 0
        for t, v in data:
            if v == 0 or v * v0 < 0:
                return t
            v0 = v

    def latency(self):
        noiselev = self.noise_level()
        print('noise level: {}'.format(noiselev))
        posdata = self.slice_range(self.posdata, 1, 2)
        v0 = posdata[0][1]
        for t, v in posdata:
            if v - v0 > noiselev:
                print('{} {}'.format(t, self.periods[1]))
                return t - self.periods[1]

    def max_velocity(self):
        return max([v[1] for v in self.slice_range(self.fveldata, 1, 2)])

    def time_to_max_velocity(self):
        return max(self.slice_range(self.fveldata, 1, 2), key = lambda i : i[1])[0]

    def max_accel(self):
        return max([v[1] for v in self.slice_range(self.facceldata, 1, 2)])

    def time_to_max_accel(self):
        return max(self.slice_range(self.facceldata, 1, 2), key = lambda i : i[1])[0] - self.periods[1]

    def max_decel(self):
        t1 = self.periods[2]
        t2 = self.xzero_time(self.slice_range(self.fveldata, 2, 3))
        return max([abs(v[1]) for v in self.slice(self.facceldata, t1, t2)])

    def time_to_max_decel(self):
        t1 = self.periods[2]
        t2 = self.xzero_time(self.slice_range(self.fveldata, 2, 3))
        return max(self.slice(self.facceldata, t1, t2), key = lambda i : abs(i[1]))[0] - t1

    def mean_accel(self):
        max_velocity = self.max_velocity()
        for t, v in self.slice_range(self.fveldata, 1, 2):
            if v >= max_velocity:
                return v / (t - self.latency())

    def mean_decel(self):
        t1 = self.periods[2]
        t2 = self.xzero_time(self.slice_range(self.fveldata, 2, 3))
        return self.max_velocity() / (t2 - t1)

    def residual_decel(self):
        t1 = self.periods[4]
        t2 = self.xzero_time(self.slice_range(self.fveldata, 4, 5))
        if t2 is None:
            t2 = self.periods[5]
        t2 = min(t1 + 0.2, t2)
        return abs(np.mean([v[1] for v in self.slice(self.facceldata, t1, t2)]))

    def estimated_snr(self):
        noise = 0
        signal = 0
        count = 0
        for _, v in self.fposdata:
            noise += math.pow(v - self.posdata[count][1], 2)
            signal += math.pow(v, 2)
            count += 1
        return 10 * math.log10(math.sqrt(signal / count) / math.sqrt(noise / count))
