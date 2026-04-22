"""
Injects auto-switch widgets into the existing Tools tab programmatically.
No Glade modifications needed.
"""

import os
from locale import gettext as _

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import GLib, Gtk

from .process_watcher import get_running_processes


class ProcessPickerDialog:
    REFRESH_INTERVAL_MS = 2000

    def __init__(self, parent_window, current_processes):
        self.current_processes = set(
            p.strip().lower() for p in current_processes.split(",") if p.strip()
        )
        self.all_processes = sorted(get_running_processes())
        self.selected = set()
        self._refresh_id = None

        self.dialog = Gtk.Dialog(
            _("Pick running processes"),
            parent_window,
            Gtk.DialogFlags.MODAL,
            (
                _("Cancel"),
                Gtk.ResponseType.CANCEL,
                _("Add selected"),
                Gtk.ResponseType.OK,
            ),
        )
        self.dialog.set_default_size(420, 480)
        self.dialog.set_default_response(Gtk.ResponseType.OK)
        self.dialog.connect("response", self._on_response)

        vbox = self.dialog.get_content_area()
        vbox.set_spacing(8)
        vbox.set_margin_top(8)
        vbox.set_margin_bottom(8)
        vbox.set_margin_start(8)
        vbox.set_margin_end(8)

        search_entry = Gtk.SearchEntry()
        search_entry.set_visible(True)
        search_entry.set_can_focus(True)
        search_entry.set_placeholder_text(_("Filter processes…"))
        vbox.pack_start(search_entry, False, False, 0)

        scrolled = Gtk.ScrolledWindow()
        scrolled.set_visible(True)
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_shadow_type(Gtk.ShadowType.IN)
        scrolled.set_vexpand(True)
        vbox.pack_start(scrolled, True, True, 0)

        self.listbox = Gtk.ListBox()
        self.listbox.set_visible(True)
        self.listbox.set_selection_mode(Gtk.SelectionMode.NONE)
        self.listbox.set_activate_on_single_click(False)
        scrolled.add(self.listbox)

        self.check_rows = {}
        self._rebuild_rows(self.all_processes)

        self.filter_entry = search_entry
        self.filter_entry.connect("search-changed", self._on_filter_changed)

        self.listbox.set_filter_func(self._filter_func)
        self.listbox.show_all()

    def _rebuild_rows(self, processes):
        for child in self.listbox.get_children():
            self.listbox.remove(child)
        self.check_rows.clear()

        for proc in processes:
            row = Gtk.ListBoxRow()
            row.set_visible(True)
            row.set_activatable(True)
            row.set_selectable(False)

            hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
            hbox.set_visible(True)
            hbox.set_margin_start(6)
            hbox.set_margin_end(6)
            hbox.set_margin_top(4)
            hbox.set_margin_bottom(4)

            check = Gtk.CheckButton()
            check.set_visible(True)
            check.set_can_focus(False)
            if proc.lower() in self.current_processes or proc in self.selected:
                check.set_active(True)
                self.selected.add(proc)
            hbox.pack_start(check, False, False, 0)

            label = Gtk.Label(label=proc)
            label.set_visible(True)
            label.set_halign(Gtk.Align.START)
            label.set_hexpand(True)
            hbox.pack_start(label, True, True, 0)

            row.add(hbox)
            self.listbox.add(row)
            self.check_rows[proc] = (row, check, label)

            check.connect("toggled", self._on_check_toggled, proc)
            row.connect("activate", self._on_row_activated, check)

    def _refresh(self):
        new_procs = sorted(get_running_processes())
        current_keys = set(self.check_rows.keys())
        new_keys = set(new_procs)
        if new_keys != current_keys:
            self._rebuild_rows(new_procs)
            self.listbox.show_all()
            self.all_processes = new_procs
        return True

    def _on_check_toggled(self, check, proc):
        if check.get_active():
            self.selected.add(proc)
        else:
            self.selected.discard(proc)

    def _on_row_activated(self, row, check):
        check.set_active(not check.get_active())

    def _on_filter_changed(self, entry):
        self.listbox.invalidate_filter()

    def _filter_func(self, row):
        text = self.filter_entry.get_text().strip().lower()
        if not text:
            return True
        for proc, (r, check, label) in self.check_rows.items():
            if r == row:
                return text in proc.lower()
        return True

    def _on_response(self, dialog, response_id):
        if self._refresh_id is not None:
            GLib.source_remove(self._refresh_id)
            self._refresh_id = None

    def run(self):
        self._refresh_id = GLib.timeout_add(self.REFRESH_INTERVAL_MS, self._refresh)
        response = self.dialog.run()
        result = sorted(self.selected) if response == Gtk.ResponseType.OK else None
        self.dialog.destroy()
        return result


def setup_auto_switch_widgets(ui, handlers):
    """
    Add an 'Auto-switch profiles' toggle and a 'Game processes' entry
    to the Tools tab ListBox. Call after ui.start().
    """
    notebook = ui.builder.get_object("main_window").get_children()[0].get_children()[1]
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
    switch_row.set_size_request(-1, 70)
    switch_row.set_selectable(False)
    switch_row.set_activatable(False)

    switch_box = Gtk.Box()
    switch_box.set_visible(True)
    switch_box.set_valign(Gtk.Align.CENTER)
    switch_box.set_spacing(64)
    switch_box.set_tooltip_text(
        _("Automatically switch profiles when a game process is detected.")
    )

    switch_label = Gtk.Label()
    switch_label.set_visible(True)
    switch_label.set_halign(Gtk.Align.START)
    switch_label.set_label(_("Auto-switch profiles"))
    switch_box.pack_start(switch_label, True, True, 0)

    auto_switch_switch = Gtk.Switch()
    auto_switch_switch.set_visible(True)
    auto_switch_switch.set_can_focus(True)
    auto_switch_switch.connect("state-set", handlers.on_auto_switch_state_set)
    switch_box.pack_end(auto_switch_switch, False, True, 0)

    switch_row.add(switch_box)
    tools_listbox.add(switch_row)

    # --- Game processes row (label above, entry + button below) ---
    entry_row = Gtk.ListBoxRow()
    entry_row.set_visible(True)
    entry_row.set_selectable(False)
    entry_row.set_activatable(False)

    entry_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
    entry_vbox.set_visible(True)
    entry_vbox.set_margin_top(6)
    entry_vbox.set_margin_bottom(6)
    entry_vbox.set_margin_start(12)
    entry_vbox.set_margin_end(12)

    entry_label = Gtk.Label()
    entry_label.set_visible(True)
    entry_label.set_halign(Gtk.Align.START)
    entry_label.set_label(_("Game processes"))
    entry_vbox.pack_start(entry_label, False, False, 0)

    hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
    hbox.set_visible(True)

    game_processes_entry = Gtk.Entry()
    game_processes_entry.set_visible(True)
    game_processes_entry.set_can_focus(True)
    game_processes_entry.set_hexpand(True)
    game_processes_entry.set_placeholder_text(_("e.g. AMS2.exe, ForzaHorizon5.exe"))
    game_processes_entry.connect("changed", handlers.on_game_processes_changed)
    game_processes_entry.connect(
        "focus-out-event", handlers.on_game_processes_focus_out
    )
    hbox.pack_start(game_processes_entry, True, True, 0)

    pick_button = Gtk.Button(label=_("Pick…"))
    pick_button.set_visible(True)
    pick_button.set_can_focus(True)
    pick_button.set_tooltip_text(_("Pick from running processes"))
    hbox.pack_end(pick_button, False, False, 0)

    entry_vbox.pack_start(hbox, False, False, 0)

    # Tag box showing selected processes as removable pills
    tag_box = Gtk.FlowBox()
    tag_box.set_visible(True)
    tag_box.set_max_children_per_line(100)
    tag_box.set_selection_mode(Gtk.SelectionMode.NONE)
    tag_box.set_min_children_per_line(0)
    entry_vbox.pack_start(tag_box, False, False, 0)

    entry_row.add(entry_vbox)
    tools_listbox.add(entry_row)

    tools_listbox.show_all()

    def refresh_tags():
        for child in tag_box.get_children():
            tag_box.remove(child)
        text = game_processes_entry.get_text().strip()
        if not text:
            tag_box.set_visible(False)
            return
        tag_box.set_visible(True)
        for part in text.split(","):
            name = part.strip()
            if not name:
                continue
            pill = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=2)
            pill.set_visible(True)
            lbl = Gtk.Label(label=name)
            lbl.set_visible(True)
            lbl.set_margin_start(6)
            lbl.set_margin_end(2)
            pill.pack_start(lbl, False, False, 0)

            btn = Gtk.Button()
            btn.set_visible(True)
            btn.set_can_focus(False)
            btn.set_relief(Gtk.ReliefStyle.NONE)
            btn.set_label("✕")
            btn.connect(
                "clicked",
                lambda _w, n=name: remove_process(n),
            )
            pill.pack_end(btn, False, False, 0)

            flow_child = Gtk.FlowBoxChild()
            flow_child.set_visible(True)
            flow_child.set_can_focus(False)
            flow_child.add(pill)
            tag_box.add(flow_child)
        tag_box.show_all()

    def remove_process(name):
        text = game_processes_entry.get_text().strip()
        parts = [p.strip() for p in text.split(",") if p.strip()]
        parts = [p for p in parts if p != name]
        game_processes_entry.set_text(", ".join(parts))
        refresh_tags()

    def on_pick_clicked(widget):
        parent = ui.builder.get_object("main_window")
        picker = ProcessPickerDialog(parent, game_processes_entry.get_text())
        result = picker.run()
        if result is not None:
            existing = [
                p.strip()
                for p in game_processes_entry.get_text().split(",")
                if p.strip()
            ]
            for proc in result:
                if proc not in existing:
                    existing.append(proc)
            game_processes_entry.set_text(", ".join(existing))
            refresh_tags()

    pick_button.connect("clicked", on_pick_clicked)

    game_processes_entry.connect("changed", lambda _w: refresh_tags())

    refresh_tags()

    ui.auto_switch_switch = auto_switch_switch
    ui.game_processes_entry = game_processes_entry

    def set_auto_switch(state):
        auto_switch_switch.set_state(bool(state))

    def get_auto_switch():
        return auto_switch_switch.get_active()

    def set_game_processes(value):
        if value is None:
            game_processes_entry.set_text("")
        else:
            game_processes_entry.set_text(str(value))
        refresh_tags()

    def get_game_processes():
        return game_processes_entry.get_text() or None

    ui.set_auto_switch = set_auto_switch
    ui.get_auto_switch = get_auto_switch
    ui.set_game_processes = set_game_processes
    ui.get_game_processes = get_game_processes
