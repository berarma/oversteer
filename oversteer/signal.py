import math
from scipy.ndimage.filters import uniform_filter1d

class Signal:

    def __init__(self, values, periods = False, resample = False):
        if resample:
            self.values = self.resample(values)
        else:
            self.values = values

        if periods:
            self.periods = [self.values[0]]
            t0, v0 = self.values[0]
            t = None
            v = None
            for t, v in self.values:
                if v - v0 != 0:
                    self.periods.append((t, v))
                    v0 = v
                    t0 = t
            if t is not None and t != t0:
                self.periods.append((t, v))

    def get_values(self):
        return self.values

    def get_value(self, t):
        return self.values[int(t * 1000)]

    def resample(self, data):
        newdata = []
        new_t = 0
        t0 = 0
        v0 = 0
        for t, v in data:
            if t > 0:
                new_t = math.ceil(t * 1000)
                if new_t > t0:
                    length = new_t - t0
                    for delta_time in range(0, length):
                        newdata.append(((t0 + delta_time) / 1000, v0))
            t0 = new_t
            v0 = v

        return newdata

    def get_period_start(self, num):
        return self.periods[num][0]

    def get_range(self, p1, p2):
        return (self.get_period_start(p1), self.get_period_start(p2))

    def get_periods(self):
        return self.periods

    def derive(self, multiplier = 1):
        newdata = [(0, 0)]
        v0 = None
        t0 = None
        for t, v in self.values:
            if v0 is not None:
                newval = (v - v0) * multiplier / (t - t0)
                newdata.append((t, newval))
            v0 = v
            t0 = t
        return Signal(newdata)

    def filter(self, average_size):
        (times, values) = zip(*self.values)
        #times = [t / 1000 for t in range(0, average_size // 2)] + [t + average_size // 2 / 1000 for t in times]
        #values = [values[0] for v in range(0, average_size // 2)] + list(values)
        filtered_data = uniform_filter1d(values, size=average_size, mode='nearest')
        newdata = list(zip(times, filtered_data))
        return Signal(newdata)

    def slice(self, t1, t2):
        return [v for v in self.values if t1 <= v[0] < t2]

    def noise_level(self, t1, t2):
        minv = 1
        maxv = -1
        sumv = 0
        count = 0
        for _, v in self.slice(t1, t2):
            sumv += v
            if v < minv:
                minv = v
            if v > maxv:
                maxv = v
            count += 1
        mean = sumv / count

        return max(mean - minv, maxv - mean)

    def xzero(self, t1, t2, offset = 0):
        data = self.slice(t1, t2)
        v0 = 0
        for t, v in data:
            if v + offset == 0 or (v + offset) * v0 < 0:
                return (t, v)
            v0 = v + offset
        return (None, None)

    def xzero_time(self, t1, t2, offset = 0):
        xzero_value = self.xzero(t1, t2, offset)
        return xzero_value[0]

    def estimated_snr(self, filtered_signal):
        noise = 0
        signal = 0
        count = 0
        for _, v in filtered_signal.get_values():
            noise += math.pow(v - self.values[count][1], 2)
            signal += math.pow(v, 2)
            count += 1
        if noise == 0:
            return 30
        return 10 * math.log10(math.sqrt(signal / count) / math.sqrt(noise / count))
