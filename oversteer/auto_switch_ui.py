"""
Injects auto-switch widgets into the existing Tools tab programmatically.
No Glade modifications needed.
"""
from locale import gettext as _
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk


def setup_auto_switch_widgets(ui, handlers):
    """
    Add an 'Auto-switch profiles' toggle and a 'Game processes' entry
    to the Tools tab ListBox. Call after ui.start().
    """
    # Find the Tools tab listbox (3rd tab = position 2)
    notebook = ui.builder.get_object('main_window').get_children()[0].get_children()[1]
    tools_content = notebook.get_nth_page(2)
    tools_listbox = tools_content.get_children()[0]

    # --- Separator ---
    sep_row = Gtk.ListBoxRow()
    sep_row.set_visible(True)
    sep_row.set_selectable(False)
    sep_row.set_activatable(False)
    sep = Gtk.Separator()
    sep.set_visible(True)
    sep_row.add(sep)
    tools_listbox.add(sep_row)

    # --- Auto-switch toggle row ---
    switch_row = Gtk.ListBoxRow()
    switch_row.set_visible(True)
    switch_row.set_height_request(70)
    switch_row.set_selectable(False)
    switch_row.set_activatable(False)

    switch_box = Gtk.Box()
    switch_box.set_visible(True)
    switch_box.set_valign(Gtk.Align.CENTER)
    switch_box.set_spacing(64)
    switch_box.set_tooltip_text(_("Automatically switch profiles when a game process is detected."))

    switch_label = Gtk.Label()
    switch_label.set_visible(True)
    switch_label.set_halign(Gtk.Align.START)
    switch_label.set_label(_("Auto-switch profiles"))
    switch_box.pack_start(switch_label, True, True, 0)

    auto_switch_switch = Gtk.Switch()
    auto_switch_switch.set_visible(True)
    auto_switch_switch.set_can_focus(True)
    auto_switch_switch.connect('state-set', handlers.on_auto_switch_state_set)
    switch_box.pack_end(auto_switch_switch, False, True, 0)

    switch_row.add(switch_box)
    tools_listbox.add(switch_row)

    # --- Game processes entry row ---
    entry_row = Gtk.ListBoxRow()
    entry_row.set_visible(True)
    entry_row.set_height_request(70)
    entry_row.set_selectable(False)
    entry_row.set_activatable(False)

    entry_box = Gtk.Box()
    entry_box.set_visible(True)
    entry_box.set_valign(Gtk.Align.CENTER)
    entry_box.set_spacing(16)
    entry_box.set_tooltip_text(_("Comma-separated process names that trigger this profile (e.g. AMS2.exe, AMS2_AVX.exe)"))

    entry_label = Gtk.Label()
    entry_label.set_visible(True)
    entry_label.set_halign(Gtk.Align.START)
    entry_label.set_label(_("Game processes"))
    entry_box.pack_start(entry_label, False, True, 0)

    game_processes_entry = Gtk.Entry()
    game_processes_entry.set_visible(True)
    game_processes_entry.set_can_focus(True)
    game_processes_entry.set_hexpand(True)
    game_processes_entry.set_placeholder_text(_("e.g. AMS2.exe, ForzaHorizon5.exe"))
    game_processes_entry.connect('changed', handlers.on_game_processes_changed)
    game_processes_entry.connect('focus-out-event', handlers.on_game_processes_focus_out)
    entry_box.pack_end(game_processes_entry, True, True, 0)

    entry_row.add(entry_box)
    tools_listbox.add(entry_row)

    tools_listbox.show_all()

    # Store references on the ui object so model flush_ui can access them
    ui.auto_switch_switch = auto_switch_switch
    ui.game_processes_entry = game_processes_entry

    # Extend ui with getter/setter for the new widgets
    def set_auto_switch(state):
        auto_switch_switch.set_state(bool(state))

    def get_auto_switch():
        return auto_switch_switch.get_active()

    def set_game_processes(value):
        if value is None:
            game_processes_entry.set_text('')
        else:
            game_processes_entry.set_text(str(value))

    def get_game_processes():
        return game_processes_entry.get_text() or None

    ui.set_auto_switch = set_auto_switch
    ui.get_auto_switch = get_auto_switch
    ui.set_game_processes = set_game_processes
    ui.get_game_processes = get_game_processes
