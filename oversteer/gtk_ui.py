import configparser
import gi
import glob
import locale
from locale import gettext as _
from pkg_resources import resource_string
import signal
import subprocess
import sys
from oversteer.wheels import Wheels
from xdg.BaseDirectory import *

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

class GtkUi:

    def __init__(self):
        signal.signal(signal.SIGINT, self.sig_int_handler)

        self.config_path = save_config_path('oversteer')
        self.profile_path = os.path.join(self.config_path, 'profiles')
        if not os.path.isdir(self.profile_path):
            os.makedirs(self.profile_path, 0o700)
        self.saved_profile = None

        self.builder = Gtk.Builder()
        self.builder.set_translation_domain('oversteer')
        self.builder.add_from_string(resource_string(__name__, 'main.ui').decode('utf-8'))
        self.builder.connect_signals(self)
        self.window = self.builder.get_object('main_window')
        self.window.show_all()

        self.device_combobox = self.builder.get_object('device')
        self.profile_combobox = self.builder.get_object('profile')
        self.save_profile_entry = self.builder.get_object('save_profile')
        self.emulation_mode_combobox = self.builder.get_object('emulation_mode')
        self.wheel_range = self.builder.get_object('wheel_range')
        self.combine_pedals = self.builder.get_object('combine_pedals')

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

        self.wheels = Wheels()
        self.refresh_window()

        Gtk.main()

    def refresh_window(self):
        model = self.device_combobox.get_model()
        if model == None:
            model = Gtk.ListStore(str, str)
        else:
            self.device_combobox.set_model(None)
            model.clear()
        for pair in self.wheels.get_devices():
            model.append(pair)
        self.device_combobox.set_model(model)
        self.device_combobox.set_active(0)

        model = self.profile_combobox.get_model()
        if model == None:
            model = Gtk.ListStore(str, str)
        else:
            self.profile_combobox.set_model(None)
            model.clear()
        model.append(['', ''])
        for profile_file in glob.iglob(os.path.join(self.profile_path, "*.ini")):
            profile_name = os.path.splitext(os.path.basename(profile_file))[0]
            model.append([profile_file, profile_name])
        self.profile_combobox.set_model(model)

        if self.saved_profile != None:
            self.profile_combobox.set_active_id(self.saved_profile)
            self.saved_profile = None

    def on_destroy(self, *args):
        Gtk.main_quit()

    def sig_int_handler(self, signal, frame):
        sys.exit(0)

    def on_about_clicked(self, *args):
        self.about_window = self.builder.get_object("about_window")
        self.about_window.show()

    def on_about_window_response(self, *args):
        self.about_window.hide()

    def format_wheel_range_value(self, scale, value):
        return round(value * 10)

    def on_device_changed(self, combobox):
        device_id = combobox.get_active_id()
        if device_id == None:
            return
        model = self.emulation_mode_combobox.get_model()
        if model == None:
            model = Gtk.ListStore(str, str)
        else:
            self.emulation_mode_combobox.set_model(None)
            model.clear()
        for key, values in enumerate(self.wheels.get_alternate_modes(device_id)):
            model.append(values[:2])
            if values[2]:
                self.emulation_mode_combobox.set_active(key)
        self.emulation_mode_combobox.set_model(model)

        self.wheel_range.set_value(self.wheels.get_range(device_id) / 10)

        self.combine_pedals.set_state(self.wheels.get_combine_pedals(device_id))

    def on_profile_changed(self, combobox):
        profile_path = combobox.get_active_id()
        if profile_path != '':
            config = configparser.ConfigParser()
            config.read(profile_path)
            self.emulation_mode_combobox.set_active_id(config['default']['mode'])
            self.wheel_range.set_value(int(config['default']['range']) / 10)
            self.combine_pedals.set_state(True if config['default']['combine_pedals'] == 'True' else False)
            self.save_profile_entry.set_text(os.path.splitext(os.path.basename(profile_path))[0])

    def on_update_clicked(self, button):
        self.wheels = Wheels()
        self.refresh_window()

    def on_test_clicked(self, button):
        subprocess.call("jstest-gtk")

    def on_apply_clicked(self, button):
        device_id = self.device_combobox.get_active_id()
        mode = self.emulation_mode_combobox.get_active_id()
        range = int(self.wheel_range.get_value() * 10)
        combine_pedals = self.combine_pedals.get_state()
        if self.wheels.is_read_only(device_id):
            subprocess.call([
                'pkexec',
                os.path.abspath(sys.argv[0]),
                '--mode', mode,
                '--range', str(range),
                '--combine-pedals' if combine_pedals else '--no-combine-pedals',
                 str(device_id)])
        else:
            self.wheels.set_mode(device_id, mode)
            self.wheels.set_range(device_id, range)
            self.wheels.set_combine_pedals(device_id, combine_pedals)

        profile_name = self.save_profile_entry.get_text()
        if profile_name != '':
            config = configparser.ConfigParser()
            config['default'] = {
                'mode': mode,
                'range': range,
                'combine_pedals': combine_pedals
            }
            profile_file = os.path.join(self.profile_path, profile_name + '.ini')
            with open(profile_file, 'w') as configfile:
                config.write(configfile)
            self.saved_profile = profile_file;

        self.wheels = Wheels()
        self.refresh_window()

        self.device_combobox.set_active_id(device_id)

