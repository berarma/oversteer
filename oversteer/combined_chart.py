from locale import gettext as _
import matplotlib
matplotlib.use("Gtk3Cairo")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_gtk3cairo import FigureCanvasGTK3Cairo as FigureCanvas
from matplotlib.backends.backend_gtk3 import NavigationToolbar2GTK3 as NavigationToolbar

class CombinedChart:

    def __init__(self, linear_chart, performance_chart):
        self.linear_chart = linear_chart
        self.performance_chart = performance_chart

    def get_canvas(self):
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2)

        ax1.title.set_text(_('Linear response test'))
        p11, = ax1.plot(*zip(*self.linear_chart.get_fixed_input_values()), label=_('Input force'), color='blue')
        p12, = ax1.plot(*zip(*self.linear_chart.get_linearity_values()), label=_('Output force'), color='purple')
        ax1.set_ylabel(_('Force level'))
        ax1.grid(True)

        ax2.axis('off')

        ax3b = ax3.twinx()
        ax3.title.set_text(_('Step test (angular velocity + position)'))
        p31, = ax3.step(*zip(*self.performance_chart.get_input_values()), label=_('Input force'), color='blue')
        p32, = ax3.step(*zip(*self.performance_chart.get_pos_values()), label=_('Angular displacement (raw)'), color='yellow')
        p33, = ax3.plot(*zip(*self.performance_chart.get_filtered_pos_values()), label=_('Angular displacement (smoothed)'), color='darkorange')
        p34, = ax3b.plot(*zip(*self.performance_chart.get_velocity_values()), label=_('Angular velocity (raw)'), color='lightgreen')
        p35, = ax3b.plot(*zip(*self.performance_chart.get_filtered_velocity_values()), label=_('Angular velocity (smoothed)'), color='green')
        ax3.set_xlabel(_('Time (s)'))
        ax3.set_ylabel(_('Position'))
        ax3b.set_ylabel(_('RPM'))
        ax3.tick_params(axis='y', labelcolor='gray')
        ax3b.tick_params(axis='y', labelcolor='green')
        ax3.grid(True)

        ax4b = ax4.twinx()
        ax4.title.set_text(_('Step test (angular acceleration)'))
        p41, = ax4.step(*zip(*self.performance_chart.get_input_values()), label=_('Input Force'), color='blue')
        p42, = ax4b.plot(*zip(*self.performance_chart.get_accel_values()), label=_('Angular acceleration (raw)'), color='orange')
        p43, = ax4b.plot(*zip(*self.performance_chart.get_filtered_accel_values()), label=_('Angular acceleration (smoothed)'), color='red')
        ax4.set_xlabel(_('Time (s)'))
        ax4b.set_ylabel(_('RPM/s'))
        ax4b.tick_params(axis='y', labelcolor='red')
        ax4.grid(True)

        props = dict(boxstyle='square', pad=1.5, facecolor='wheat', alpha=0.5)
        text = [
            _('Latency = {:.0f} ms'),
            _('Max. velocity = {:.0f} RPM'),
            _('Mean accel. = {:.0f} RPM/s'),
            _('Mean decel. = {:.0f} RPM/s'),
            _('Max. accel. = {:.0f} RPM/s'),
            _('Time max. accel. = {:.0f} ms'),
            _('Max. decel. = {:.0f} RPM/s'),
            _('Time max. decel. = {:.0f} ms'),
            _('Residual decel. = {:.0f} RPM/s'),
            _('Estimated SNR = {:.0f} dB'),
            _('Min. force level = {:.1f} %'),
        ]
        values = [
            self.performance_chart.get_latency() * 1000,
            self.performance_chart.get_max_velocity(),
            self.performance_chart.get_mean_accel(),
            self.performance_chart.get_mean_decel(),
            self.performance_chart.get_max_accel(),
            self.performance_chart.get_time_to_max_accel() * 1000,
            self.performance_chart.get_max_decel(),
            self.performance_chart.get_time_to_max_decel() * 1000,
            self.performance_chart.get_residual_decel(),
            self.performance_chart.get_estimated_snr(),
            self.linear_chart.get_minimum_level_percent(),
        ]
        ax2.text(0, 0.9, '\n'.join(text).format(*values), transform=ax2.transAxes, fontsize=10, verticalalignment='top', bbox=props)
        fig.subplots_adjust(left=0.1, right=0.8)

        subplots = [p11, p12, p32, p33, p34, p35, p42, p43]
        plt.figlegend(subplots, [p.get_label() for p in subplots], loc='upper center', mode=None, ncol=3)

        self.align_yaxis(ax3, 0, ax3b, 0)
        self.align_yaxis(ax4, 0, ax4b, 0)

        canvas = FigureCanvas(fig)

        return canvas

    def get_navigation_toolbar(self, canvas):
        return NavigationToolbar(canvas)

    def align_yaxis(self, ax1, v1, ax2, v2):
        """adjust ax2 ylimit so that v2 in ax2 is aligned to v1 in ax1"""
        _, y1 = ax1.transData.transform((0, v1))
        _, y2 = ax2.transData.transform((0, v2))
        inv = ax2.transData.inverted()
        _, dy = inv.transform((0, 0)) - inv.transform((0, y1-y2))
        miny, maxy = ax2.get_ylim()
        ax2.set_ylim(miny+dy, maxy+dy)
