from locale import gettext as _
import gi
import logging
import math
import os
from .gtk_handlers import GtkHandlers

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GLib

class GtkUi:

    def __init__(self, controller):
        self.controller = controller
        handlers = GtkHandlers(self, controller)

        self.ffbmeter_timer = False

        style_provider = Gtk.CssProvider()
        style_provider.load_from_path(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'main.css'))
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(),
            style_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

        self.builder = Gtk.Builder()
        self.builder.set_translation_domain('oversteer')
        self.builder.add_from_file(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'main.ui'))

        self._set_builder_objects()

        self._set_markers()

        cell_renderer = Gtk.CellRendererText()
        self.device_combobox.pack_start(cell_renderer, True)
        self.device_combobox.add_attribute(cell_renderer, 'text', 1)
        self.device_combobox.set_id_column(0)

        cell_renderer = Gtk.CellRendererText()
        self.profile_combobox.pack_start(cell_renderer, True)
        self.profile_combobox.add_attribute(cell_renderer, 'text', 1)
        self.profile_combobox.set_id_column(0)

        cell_renderer = Gtk.CellRendererText()
        self.emulation_mode_combobox.pack_start(cell_renderer, True)
        self.emulation_mode_combobox.add_attribute(cell_renderer, 'text', 1)
        self.emulation_mode_combobox.set_id_column(0)

        self.set_range_overlay('never')

        self.builder.connect_signals(handlers)

    def main(self):
        self.window.show_all()
        Gtk.main()

    def safe_call(self, callback, *args):
        GLib.idle_add(callback, *args)

    def confirmation_dialog(self, message):
        dialog = Gtk.MessageDialog(self.window, 0,
                Gtk.MessageType.WARNING, Gtk.ButtonsType.OK_CANCEL, message)
        response = dialog.run()
        dialog.destroy()
        return response == Gtk.ResponseType.OK

    def info_dialog(self, message, secondary_text = ''):
        dialog = Gtk.MessageDialog(self.preferences_window, 0, Gtk.MessageType.INFO,
                Gtk.ButtonsType.OK, message)
        dialog.format_secondary_text(secondary_text)
        dialog.run()
        dialog.destroy()

    def update(self):
        self.window.queue_draw()

    def set_app_version(self, version):
        self.about_window.set_version(version)

    def set_app_icon(self, icon):
        if not os.access(icon, os.R_OK):
            logging.debug("Icon not found: " + icon)
            return
        self.window.set_icon_from_file(icon)

    def set_languages(self, languages):
        cell_renderer = Gtk.CellRendererText()
        self.languages_combobox.pack_start(cell_renderer, True)
        self.languages_combobox.add_attribute(cell_renderer, 'text', 1)
        self.languages_combobox.set_id_column(0)
        model = self.languages_combobox.get_model()
        model = Gtk.ListStore(str, str)
        for pair in languages:
            model.append(pair)
        self.languages_combobox.set_model(model)

    def set_language(self, language):
        self.languages_combobox.set_active_id(language)

    def set_check_permissions(self, state):
        self.check_permissions.set_state(state)

    def set_device_id(self, device_id):
        self.device_combobox.set_active_id(device_id)

    def set_devices(self, devices):
        model = self.device_combobox.get_model()
        if model is None:
            model = Gtk.ListStore(str, str)
        else:
            self.device_combobox.set_model(None)
            model.clear()
        if devices:
            for pair in devices:
                model.append(pair)
            self.device_combobox.set_model(model)
            if self.device_combobox.get_active() == -1:
                self.device_combobox.set_active(0)

    def set_profiles(self, profiles):
        model = self.profile_combobox.get_model()
        if model is None:
            model = Gtk.ListStore(str, str)
        else:
            self.profile_combobox.set_model(None)
            model.clear()
        model.append(['', ''])
        for profile_file in profiles:
            profile_name = os.path.splitext(os.path.basename(profile_file))[0]
            model.append([profile_file, profile_name])
        self.profile_combobox.set_model(model)

    def set_profile(self, profile):
        self.profile_combobox.set_active_id(profile)

    def set_modes(self, modes, startup = False):
        if startup:
            if modes is None:
                self.emulation_mode_combobox.set_sensitive(False)
                return
            else:
                self.emulation_mode_combobox.set_sensitive(True)
        model = self.emulation_mode_combobox.get_model()
        if model is None:
            model = Gtk.ListStore(str, str)
        else:
            self.emulation_mode_combobox.set_model(None)
            model.clear()
        for key, values in enumerate(modes):
            model.append(values[:2])
            if values[2]:
                self.emulation_mode_combobox.set_active(key)
        self.emulation_mode_combobox.set_model(model)

    def set_mode(self, mode):
        self.emulation_mode_combobox.set_active_id(mode)

    def set_range(self, range):
        if range is None:
            self.wheel_range.set_sensitive(False)
            self.wheel_range_overlay_always.set_sensitive(False)
            self.wheel_range_overlay_auto.set_sensitive(False)
            return
        else:
            self.wheel_range.set_sensitive(True)
            self.wheel_range_overlay_always.set_sensitive(True)
            self.wheel_range_overlay_auto.set_sensitive(True)
            range = int(range) / 10
            self.wheel_range.set_value(range)
            range = str(round(range * 10))
            self.overlay_wheel_range.set_label(range)

    def set_combine_pedals(self, combine_pedals):
        if combine_pedals is None:
            self.combine_brakes.set_sensitive(False)
            self.combine_clutch.set_sensitive(False)
        else:
            self.combine_brakes.set_sensitive(True)
            self.combine_clutch.set_sensitive(True)
        if combine_pedals == 1:
            self.combine_brakes.set_active(True)
        elif combine_pedals == 2:
            self.combine_clutch.set_active(True)
        else:
            self.combine_none.set_active(True)

    def set_autocenter(self, autocenter):
        self.autocenter.set_value(int(autocenter))

    def set_ff_gain(self, ff_gain):
        self.ff_gain.set_value(int(ff_gain))

    def set_spring_level(self, level):
        if level is None:
            self.ff_spring_level.set_sensitive(False)
        else:
            self.ff_spring_level.set_sensitive(True)
            self.ff_spring_level.set_value(int(level))

    def set_damper_level(self, level):
        if level is None:
            self.ff_damper_level.set_sensitive(False)
        else:
            self.ff_damper_level.set_sensitive(True)
            self.ff_damper_level.set_value(int(level))

    def set_friction_level(self, level):
        if level is None:
            self.ff_friction_level.set_sensitive(False)
        else:
            self.ff_friction_level.set_sensitive(True)
            self.ff_friction_level.set_value(int(level))

    def set_ffb_leds(self, value):
        if value is None:
            self.ffbmeter_leds.set_sensitive(False)
        else:
            self.ffbmeter_leds.set_sensitive(True)
            self.ffbmeter_leds.set_active(bool(value))

    def set_ffb_overlay(self, state):
        if state is None:
            self.set_ffbmeter_overlay_visibility(False)
        else:
            self.set_ffbmeter_overlay_visibility(True)
            self.ffbmeter_overlay.set_active(state)
            self.update_overlay()

    def set_range_overlay(self, id):
        self.wheel_range_overlay_never.set_active(False)
        self.wheel_range_overlay_always.set_active(False)
        self.wheel_range_overlay_auto.set_active(False)
        if id == 'always':
            self.wheel_range_overlay_always.set_active(True)
        elif id == 'auto':
            self.wheel_range_overlay_auto.set_active(True)
        else:
            self.wheel_range_overlay_never.set_active(True)

    def set_use_buttons(self, state):
        return self.wheel_buttons.set_state(state)

    def set_new_profile_name(self, name):
        self.new_profile_name.set_text(name)

    def set_steering_input(self, value):
        if value < 32768:
            self.steering_left_input.set_value(self._round_input((32768 - value) / 32768, 3))
            self.steering_right_input.set_value(0)
        else:
            self.steering_left_input.set_value(0)
            self.steering_right_input.set_value(self._round_input((value - 32768) / 32768, 3))

    def set_clutch_input(self, value):
        self.clutch_input.set_value(self._round_input((255 - value) / 255, 2))

    def set_accelerator_input(self, value):
        self.accelerator_input.set_value(self._round_input((255 - value) / 255, 2))

    def set_brakes_input(self, value):
        self.brakes_input.set_value(self._round_input((255 - value) / 255, 2))

    def set_hatx_input(self, value):
        if value < 0:
            self.hat_left_input.set_value(-value)
            self.hat_right_input.set_value(0)
        else:
            self.hat_left_input.set_value(0)
            self.hat_right_input.set_value(value)

    def set_haty_input(self, value):
        if value < 0:
            self.hat_up_input.set_value(-value)
            self.hat_down_input.set_value(0)
        else:
            self.hat_up_input.set_value(0)
            self.hat_down_input.set_value(value)

    def set_btn_input(self, index, value, wait = None):
        if wait is not None:
            GLib.timeout_add(wait, lambda index=index, value=value: self.set_btn_input(index, value))
        else:
            self.btn_input[index].set_value(value)
        return False

    def set_ffbmeter_overlay_visibility(self, state):
        self.ffbmeter_overlay.set_sensitive(state)

    def set_define_buttons_text(self, text):
        self.start_define_buttons.set_label(text)

    def reset_define_buttons_text(self):
        self.start_define_buttons.set_label(self.define_buttons_text)

    def update_overlay(self, auto = False):
        ffbmeter_overlay = self.ffbmeter_overlay.get_active()
        if self.wheel_range_overlay_never.get_active():
            wheel_range_overlay = 'never'
        elif self.wheel_range_overlay_always.get_active():
            wheel_range_overlay = 'always'
        elif self.wheel_range_overlay_auto.get_active():
            wheel_range_overlay = 'auto'
        if ffbmeter_overlay or wheel_range_overlay == 'always' or (wheel_range_overlay == 'auto' and auto):
            if not self.overlay_window.props.visible:
                self.overlay_window.show()
                self.overlay_window.move(self.overlay_window_pos[0], self.overlay_window_pos[1])
            if not self.ffbmeter_timer and self.overlay_window.props.visible and ffbmeter_overlay:
                self.ffbmeter_timer = True
                GLib.timeout_add(250, self._update_ffbmeter_overlay)
            if ffbmeter_overlay:
                self._ffbmeter_overlay.show()
            else:
                self._ffbmeter_overlay.hide()
            if wheel_range_overlay == 'always' or (wheel_range_overlay == 'auto' and auto):
                self._wheel_range_overlay.show()
            else:
                self._wheel_range_overlay.hide()
        else:
            self.overlay_window.hide()

    def set_overlay_window_pos(self, position):
        self.overlay_window_pos = position
        self.overlay_window.move(position[0], position[1])

    def update_overlay_window_pos(self, position):
        self.overlay_window_pos = position

    def _update_ffbmeter_overlay(self):
        if not self.overlay_window.props.visible or not self.ffbmeter_overlay.props.visible:
            self.ffbmeter_timer = False
            return False
        level = self.controller.read_ffbmeter()
        if level < 2458: # < 7.5%
            led_states = 0
        elif level < 8192: # < 25%
            led_states = 1
        elif level < 16384: # < 50%
            led_states = 3
        elif level < 24576: # < 75%
            led_states = 7
        elif level < 29491: # < 90%
            led_states = 15
        elif level <= 32768: # <= 100%
            led_states = 31
        elif level < 36045: # < 110%
            led_states = 30
        elif level < 40960: # < 125%
            led_states = 28
        elif level < 49152: # < 150%
            led_states = 24
        else:
            led_states = 16
        self.overlay_led_0.set_value(led_states & 1)
        self.overlay_led_1.set_value((led_states >> 1) & 1)
        self.overlay_led_2.set_value((led_states >> 2) & 1)
        self.overlay_led_3.set_value((led_states >> 3) & 1)
        self.overlay_led_4.set_value((led_states >> 4) & 1)
        return True

    def _round_input(self, value, decimals = 0):
        multiplier = 10 ** decimals
        return math.floor(value * multiplier) / multiplier

    def _screen_changed(self, widget, old_screen, userdata=None):
        screen = self.overlay_window.get_screen()
        visual = screen.get_rgba_visual()
        self.overlay_window.set_visual(visual)

    def _set_builder_objects(self):
        self.window = self.builder.get_object('main_window')
        self.about_window = self.builder.get_object('about_window')
        self.preferences_window = self.builder.get_object('preferences_window')
        self.overlay_window = self.builder.get_object('overlay_window')
        self.overlay_window.set_keep_above(True)
        self.overlay_window.connect("screen-changed", self._screen_changed)
        self._screen_changed(self.overlay_window, None)

        self.languages_combobox = self.builder.get_object('languages')
        self.check_permissions = self.builder.get_object('check_permissions')

        self.device_combobox = self.builder.get_object('device')
        self.profile_combobox = self.builder.get_object('profile')
        self.new_profile_name = self.builder.get_object('new_profile_name')
        self.emulation_mode_combobox = self.builder.get_object('emulation_mode')
        self.change_emulation_mode_button = self.builder.get_object('change_emulation_mode')
        self.wheel_range = self.builder.get_object('wheel_range')
        self.combine_none = self.builder.get_object('combine_none')
        self.combine_brakes = self.builder.get_object('combine_brakes')
        self.combine_clutch = self.builder.get_object('combine_clutch')
        self.autocenter = self.builder.get_object('autocenter')
        self.ff_gain = self.builder.get_object('ff_gain')
        self.ff_spring_level = self.builder.get_object('ff_spring_level')
        self.ff_damper_level = self.builder.get_object('ff_damper_level')
        self.ff_friction_level = self.builder.get_object('ff_friction_level')
        self.ffbmeter_leds = self.builder.get_object('ffbmeter_leds')
        self.ffbmeter_overlay = self.builder.get_object('ffbmeter_overlay')
        self.wheel_range_overlay_never = self.builder.get_object('wheel_range_overlay_never')
        self.wheel_range_overlay_always = self.builder.get_object('wheel_range_overlay_always')
        self.wheel_range_overlay_auto = self.builder.get_object('wheel_range_overlay_auto')
        self._ffbmeter_overlay = self.builder.get_object('_ffbmeter_overlay')
        self._wheel_range_overlay = self.builder.get_object('_wheel_range_overlay')
        self.overlay_wheel_range = self.builder.get_object('overlay_wheel_range')
        self.overlay_led_0 = self.builder.get_object('overlay_led_0')
        self.overlay_led_1 = self.builder.get_object('overlay_led_1')
        self.overlay_led_2 = self.builder.get_object('overlay_led_2')
        self.overlay_led_3 = self.builder.get_object('overlay_led_3')
        self.overlay_led_4 = self.builder.get_object('overlay_led_4')
        self.wheel_buttons = self.builder.get_object('wheel_buttons')
        self.start_define_buttons = self.builder.get_object('start_define_buttons')
        self.define_buttons_text = self.start_define_buttons.get_label()

        self.steering_left_input = self.builder.get_object('steering_left_input')
        self.steering_right_input = self.builder.get_object('steering_right_input')
        self.clutch_input = self.builder.get_object('clutch_input')
        self.accelerator_input = self.builder.get_object('accelerator_input')
        self.brakes_input = self.builder.get_object('brakes_input')
        self.hat_up_input = self.builder.get_object('hat_up_input')
        self.hat_down_input = self.builder.get_object('hat_down_input')
        self.hat_left_input = self.builder.get_object('hat_left_input')
        self.hat_right_input = self.builder.get_object('hat_right_input')
        self.btn_input = [None] * 25
        for i in range(0, 25):
            self.btn_input[i] = self.builder.get_object('btn' + str(i) + '_input')

    def _set_markers(self):
        self.wheel_range.add_mark(18, Gtk.PositionType.BOTTOM, '180')
        self.wheel_range.add_mark(27, Gtk.PositionType.BOTTOM, '270')
        self.wheel_range.add_mark(36, Gtk.PositionType.BOTTOM, '360')
        self.wheel_range.add_mark(45, Gtk.PositionType.BOTTOM, '450')
        self.wheel_range.add_mark(54, Gtk.PositionType.BOTTOM, '540')
        self.wheel_range.add_mark(72, Gtk.PositionType.BOTTOM, '720')
        self.wheel_range.add_mark(90, Gtk.PositionType.BOTTOM, '900')
        self.autocenter.add_mark(20, Gtk.PositionType.BOTTOM, '20')
        self.autocenter.add_mark(40, Gtk.PositionType.BOTTOM, '40')
        self.autocenter.add_mark(60, Gtk.PositionType.BOTTOM, '60')
        self.autocenter.add_mark(80, Gtk.PositionType.BOTTOM, '80')
        self.autocenter.add_mark(100, Gtk.PositionType.BOTTOM, '100')
        self.ff_gain.add_mark(20, Gtk.PositionType.BOTTOM, '20')
        self.ff_gain.add_mark(40, Gtk.PositionType.BOTTOM, '40')
        self.ff_gain.add_mark(60, Gtk.PositionType.BOTTOM, '60')
        self.ff_gain.add_mark(80, Gtk.PositionType.BOTTOM, '80')
        self.ff_gain.add_mark(100, Gtk.PositionType.BOTTOM, '100')
        self.ff_spring_level.add_mark(20, Gtk.PositionType.BOTTOM, '20')
        self.ff_spring_level.add_mark(40, Gtk.PositionType.BOTTOM, '40')
        self.ff_spring_level.add_mark(60, Gtk.PositionType.BOTTOM, '60')
        self.ff_spring_level.add_mark(80, Gtk.PositionType.BOTTOM, '80')
        self.ff_spring_level.add_mark(100, Gtk.PositionType.BOTTOM, '100')
        self.ff_damper_level.add_mark(20, Gtk.PositionType.BOTTOM, '20')
        self.ff_damper_level.add_mark(40, Gtk.PositionType.BOTTOM, '40')
        self.ff_damper_level.add_mark(60, Gtk.PositionType.BOTTOM, '60')
        self.ff_damper_level.add_mark(80, Gtk.PositionType.BOTTOM, '80')
        self.ff_damper_level.add_mark(100, Gtk.PositionType.BOTTOM, '100')
        self.ff_friction_level.add_mark(20, Gtk.PositionType.BOTTOM, '20')
        self.ff_friction_level.add_mark(40, Gtk.PositionType.BOTTOM, '40')
        self.ff_friction_level.add_mark(60, Gtk.PositionType.BOTTOM, '60')
        self.ff_friction_level.add_mark(80, Gtk.PositionType.BOTTOM, '80')
        self.ff_friction_level.add_mark(100, Gtk.PositionType.BOTTOM, '100')

