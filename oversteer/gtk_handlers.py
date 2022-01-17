import gi
from locale import gettext as _
import threading
import traceback
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk

class GtkHandlers:

    @property
    def model(self):
        return self.controller.model

    def __init__(self, ui, controller):
        self.ui = ui
        self.controller = controller

    def format_wheel_range_value(self, scale, value):
        return str(round(value * 10))

    def on_main_window_destroy(self, *args):
        self.ui.quit()

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

    def on_pedals_changed(self, widget):
        pedals_id = widget.get_active_id()
        if pedals_id is not None:
            self.controller.change_pedals(pedals_id)

    def on_update_clicked(self, button):
        self.controller.populate_window()
        self.ui.update()

    def on_change_emulation_mode_clicked(self, widget):
        mode = self.ui.emulation_mode_combobox.get_active_id()
        self.model.set_mode(mode)
        self.model.flush_ui()
        self.ui.change_emulation_mode_button.set_sensitive(False)

    def on_emulation_mode_changed(self, widget):
        self.ui.change_emulation_mode_button.set_sensitive(True)

    def on_wheel_range_value_changed(self, widget):
        wrange = int(widget.get_value() * 10)
        self.model.set_range(wrange)
        self.ui.overlay_wheel_range.set_label(str(wrange))

    def on_overlay_decrange_clicked(self, widget):
        adjustment = self.ui.wheel_range.get_adjustment()
        step = adjustment.get_step_increment()
        self.ui.wheel_range.set_value(self.ui.wheel_range.get_value() - step)
        wrange = int(self.ui.wheel_range.get_value() * 10)
        self.ui.overlay_wheel_range.set_label(str(wrange))

    def on_overlay_incrange_clicked(self, widget):
        adjustment = self.ui.wheel_range.get_adjustment()
        step = adjustment.get_step_increment()
        self.ui.wheel_range.set_value(self.ui.wheel_range.get_value() + step)
        wrange = int(self.ui.wheel_range.get_value() * 10)
        self.ui.overlay_wheel_range.set_label(str(wrange))

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
        self.model.set_range_overlay(self.ui.get_wheel_range_overlay())
        self.ui.update_overlay()

    def on_start_define_buttons_clicked(self, widget):
        self.controller.start_stop_button_setup()

    def on_wheel_buttons_state_set(self, widget, state):
        self.model.set_use_buttons(state)

    def on_center_wheel_state_set(self, widget, state):
        threading.Thread(target = self.model.set_center_wheel, args = [state], daemon = True).start()

    def on_profile_changed(self, combobox):
        self.controller.load_profile(combobox.get_active_id())

    def on_save_profile_clicked(self, widget):
        profile_name = self.ui.profile_combobox.get_active_id()
        self.controller.save_profile(profile_name)

    def on_new_profile_clicked(self, widget):
        self.ui.new_profile_name_entry.set_text('')
        self.ui.new_profile_name_entry.show()
        self.ui.new_profile_name_entry.grab_focus()

    def on_new_profile_focus_out(self, widget, event):
        widget.hide()

    def on_new_profile_key_release(self, widget, event):
        if event.keyval == Gdk.KEY_Escape:
            widget.hide()

    def on_new_profile_activate(self, widget):
        widget.hide()
        profile_name = widget.get_text()
        try:
            self.controller.save_profile(profile_name, True)
            self.ui.profile_listbox_add(profile_name)
            self.ui.update_profiles_combobox()
        except (KeyboardInterrupt, SystemExit):
            raise
        except Exception as e:
            if str(e) != '':
                self.ui.error_dialog(_('Error creating profile'), traceback.format_exc())

    def on_rename_profile_clicked(self, widget):
        row = self.ui.profile_listbox.get_selected_row()
        if row is None:
            return

        def on_rename_profile_focus_out(widget, event):
            entry.disconnect_by_func(on_rename_profile_focus_out)
            row.remove(widget)
            row.add(label)

        def on_rename_profile_key_release(widget, event):
            if event.keyval == Gdk.KEY_Escape:
                entry.disconnect_by_func(on_rename_profile_focus_out)
                row.remove(widget)
                row.add(label)

        def on_rename_profile_activate(widget):
            entry.disconnect_by_func(on_rename_profile_focus_out)
            source_profile_name = label.get_text()
            target_profile_name = widget.get_text()
            row.remove(widget)
            row.add(label)
            try:
                self.controller.rename_profile(source_profile_name, target_profile_name)
                label.set_text(target_profile_name)
                self.ui.profile_listbox.invalidate_sort()
                self.ui.update_profiles_combobox()
            except (KeyboardInterrupt, SystemExit):
                raise
            except Exception as e:
                self.ui.error_dialog(_('Error renaming profile'), str(e))
        entry = Gtk.Entry()
        entry.connect('activate', on_rename_profile_activate)
        entry.connect('focus-out-event', on_rename_profile_focus_out)
        entry.connect('key-release-event', on_rename_profile_key_release)
        label = row.get_children()[0]
        row.remove(label)
        text = label.get_text()
        entry.set_text(text)
        row.add(entry)
        entry.show()
        entry.grab_focus()

    def on_delete_profile_clicked(self, widget):
        row = self.ui.profile_listbox.get_selected_row()
        if row is None:
            return
        profile_name = row.get_children()[0].get_text()
        try:
            self.controller.delete_profile(profile_name)
            self.ui.profile_listbox.remove(row)
            self.ui.update_profiles_combobox()
        except (KeyboardInterrupt, SystemExit):
            raise
        except Exception as e:
            if str(e) != '':
                self.ui.error_dialog(_('Error deleting profile'), str(e))

    def on_import_profile_clicked(self, widget):
        profile_file = self.ui.file_chooser(_('Choose profile file to import'), 'open')
        if profile_file is None:
            return
        try:
            profile_name = self.controller.import_profile(profile_file)
            self.ui.profile_listbox_add(profile_name)
            self.ui.update_profiles_combobox()
        except (KeyboardInterrupt, SystemExit):
            raise
        except Exception as e:
            self.ui.error_dialog(_('Error importing profile'), str(e))

    def on_export_profile_clicked(self, widget):
        row = self.ui.profile_listbox.get_selected_row()
        if row is None:
            return
        profile_name = row.get_children()[0].get_text()
        export_file = self.ui.file_chooser(_('Export profile to'), 'save', profile_name + '.ini')
        if export_file is None:
            return
        try:
            self.controller.export_profile(profile_name, export_file)
        except (KeyboardInterrupt, SystemExit):
            raise
        except Exception as e:
            self.ui.error_dialog(_('Error exporting profile'), str(e))

    def on_test_start_clicked(self, widget):
        self.controller.start_test()

    def reset_test_start_button(self):
        self.ui.test_start_button.set_text(self.default_test_start_button_text)

    def on_test_open_chart_button_clicked(self, widget):
        self.controller.open_test_chart()

    def on_test_import_csv_button_clicked(self, widget):
        self.controller.import_test_values()

    def on_test_export_csv_button_clicked(self, widget):
        self.controller.export_test_values()

    def on_test_chart_window_delete_event(self, widget, event):
        self.ui.test_chart_window.hide()
        self.ui.test_open_chart_button.set_sensitive(True)
        return True

    def on_test_panel_back_clicked(self, widget):
        self.controller.prev_test()

    def on_test_panel_run_clicked(self, widget):
        self.controller.run_test()

    def on_start_app_manually_state_set(self, widget, state):
        self.model.set_start_app_manually(state)

    def on_start_app_clicked(self, widget):
        self.controller.start_app()
