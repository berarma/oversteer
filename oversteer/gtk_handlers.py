import gi

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GLib

class GtkHandlers:

    @property
    def model(self):
        return self.controller.model

    def __init__(self, ui, controller):
        self.ui = ui
        self.controller = controller

    def format_wheel_range_value(self, scale, value):
        return str(round(value * 10))

    def on_overlay_window_configure(self, window, event):
        if event.type == Gdk.EventType.CONFIGURE:
            self.ui.update_overlay_window_pos((event.x, event.y))

    def on_main_window_destroy(self, *args):
        Gtk.main_quit()

    def on_preferences_window_delete_event(self, *args):
        self.controller.on_close_preferences()
        self.ui.preferences_window.hide()
        return True

    def on_preferences_clicked(self, *args):
        self.ui.preferences_window.show()

    def on_cancel_preferences_clicked(self, *args):
        self.controller.on_close_preferences()
        self.ui.preferences_window.hide()

    def on_about_clicked(self, *args):
        self.ui.about_window.show()

    def on_about_window_response(self, *args):
        self.ui.about_window.hide()

    def on_about_window_delete_event(self, *args):
        self.ui.about_window.hide()
        return True

    def on_device_changed(self, widget):
        device_id = widget.get_active_id()
        if device_id is not None:
            self.controller.change_device(device_id)

    def on_profile_changed(self, combobox):
        self.controller.load_profile(combobox.get_active_id())

    def on_save_profile_as_clicked(self, widget):
        profile_name = self.ui.new_profile_name.get_text()
        self.controller.save_profile_as(profile_name)

    def on_save_profile_clicked(self, widget):
        profile_file = self.ui.profile_combobox.get_active_id()
        self.controller.save_profile(profile_file)

    def on_update_clicked(self, button):
        self.controller.populate_window()
        self.ui.update()

    def on_change_emulation_mode_clicked(self, widget):
        mode = self.ui.emulation_mode_combobox.get_active_id()
        self.model.set_mode(mode)
        self.ui.change_emulation_mode_button.set_sensitive(False)

    def on_emulation_mode_changed(self, widget):
        self.ui.change_emulation_mode_button.set_sensitive(True)

    def on_wheel_range_value_changed(self, widget):
        range = widget.get_value() * 10
        self.model.set_range(range)
        self.ui.overlay_wheel_range.set_label(str(range))

    def on_overlay_decrange_clicked(self, widget):
        adjustment = self.ui.wheel_range.get_adjustment()
        step = adjustment.get_step_increment()
        self.ui.wheel_range.set_value(self.ui.wheel_range.get_value() - step)
        range = self.ui.wheel_range.get_value() * 10
        self.ui.overlay_wheel_range.set_label(range)

    def on_overlay_incrange_clicked(self, widget):
        adjustment = self.ui.wheel_range.get_adjustment()
        step = adjustment.get_step_increment()
        self.ui.wheel_range.set_value(self.ui.wheel_range.get_value() + step)
        range = self.ui.wheel_range.get_value() * 10
        self.ui.overlay_wheel_range.set_label(range)

    def on_combine_none_clicked(self, widget):
        self.model.set_combine_pedals(0)

    def on_combine_brakes_clicked(self, widget):
        self.model.set_combine_pedals(1)

    def on_combine_clutch_clicked(self, widget):
        self.model.set_combine_pedals(2)

    def on_ff_gain_value_changed(self, widget):
        ff_gain = int(widget.get_value())
        self.model.set_ff_gain(ff_gain)

    def on_autocenter_value_changed(self, widget):
        autocenter = int(widget.get_value())
        self.model.set_autocenter(autocenter)

    def on_delete_profile_clicked(self, widget):
        profile_file = self.ui.profile_combobox.get_active_id()
        self.controller.delete_profile(profile_file)

    def on_check_permissions_state_set(self, widget, state):
        self.controller.set_check_permissions(state)

    def on_languages_changed(self, widget):
        self.controller.set_locale(widget.get_active_id())

    def on_ff_spring_level_value_changed(self, widget):
        self.model.set_spring_level(widget.get_value())

    def on_ff_damper_level_value_changed(self, widget):
        self.model.set_damper_level(widget.get_value())

    def on_ff_friction_level_value_changed(self, widget):
        self.model.set_friction_level(widget.get_value())

    def on_ffbmeter_leds_clicked(self, widget):
        self.model.set_ffb_leds(widget.get_active())

    def on_ffbmeter_overlay_clicked(self, widget):
        state = widget.get_active()
        self.model.set_ffb_overlay(state)
        if state:
            self.ui._ffbmeter_overlay.show()
        else:
            self.ui._ffbmeter_overlay.hide()
        self.ui.update_overlay()

    def on_wheel_range_overlay_clicked(self, widget):
        self.model.set_range_overlay(widget.get_active())
        self.ui.update_overlay()

    def on_start_define_buttons_clicked(self, widget):
        self.controller.start_stop_button_setup()

    def on_wheel_buttons_state_set(self, widget, state):
        self.model.set_use_buttons(state)

