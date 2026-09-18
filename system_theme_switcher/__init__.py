# SPDX-License-Identifier: GPL-3.0-or-later
import time

import bpy
from bpy.props import BoolProperty, EnumProperty, StringProperty
from bpy.app.handlers import persistent

from .appearance import AppearanceProbe
from . import themes, transition

_probe = AppearanceProbe()
_original = None
_applied = None
_status = "Waiting for macOS appearance"
_next_poll = 0.0
_force = True


def preferences():
    addon = bpy.context.preferences.addons.get(__package__)
    return addon.preferences if addon else None


def changed(_self, _context):
    global _force, _next_poll
    _force = True
    _next_poll = 0.0
    if _self is not None and not _self.enabled:
        transition.stop(finish=True)


def sync_mode(mode, prefs):
    """Apply only on appearance/selection changes, or an explicit sync request."""
    global _original, _applied, _status, _force
    selected = prefs.light_theme if mode == "LIGHT" else prefs.dark_theme
    key = (mode, selected)
    if _force or key != _applied:
        before = transition.begin(selected)
        if _original is None:
            _original = before
        _applied = key
        _force = False
    _status = f"{mode.title()} — {themes.theme_label(selected)}"


def tick():
    global _status, _next_poll
    prefs = preferences()
    if prefs is None:
        return 1.0
    previous = _status
    try:
        if not prefs.enabled:
            _probe.close()
            _status = "Paused — current theme kept"
            return 1.0
        if time.monotonic() < _next_poll:
            return 0.25
        if _probe.process is None:
            _probe.start()
        mode = _probe.poll()
        if mode is not None:
            sync_mode(mode, prefs)
            _next_poll = time.monotonic() + 2.0
    except Exception as exc:
        _probe.close()
        _status = f"Error: {exc}"
        _next_poll = time.monotonic() + 5.0
    finally:
        if _status != previous:
            themes.redraw()
    return 0.25


class STS_Preferences(bpy.types.AddonPreferences):
    bl_idname = __package__

    enabled: BoolProperty(
        name="Follow macOS Appearance", default=True, update=changed,
        description="Switch the chosen themes when macOS changes light or dark appearance",
    )
    light_theme: StringProperty(default=themes.BUILTIN_LIGHT, update=changed)
    dark_theme: StringProperty(default=themes.BUILTIN_DARK, update=changed)

    def draw(self, _context):
        layout = self.layout
        layout.prop(self, "enabled")
        for mode, menu in (("LIGHT", "STS_MT_light"), ("DARK", "STS_MT_dark")):
            selected = self.light_theme if mode == "LIGHT" else self.dark_theme
            row = layout.row()
            row.label(text=f"{mode.title()} theme")
            row.menu(menu, text=themes.theme_label(selected))
        row = layout.row(align=True)
        row.enabled = self.enabled
        row.operator("sts.sync", icon='FILE_REFRESH')
        row = layout.row()
        row.enabled = _original is not None
        row.operator("sts.restore", icon='LOOP_BACK')
        box = layout.box()
        box.label(text=_status, icon='ERROR' if _status.startswith("Error:") else 'INFO')
        layout.label(text="Checks about every 2 seconds while Blender is running.")
        layout.label(text="Restore is available for this session only.")


class STS_OT_choose(bpy.types.Operator):
    bl_idname = "sts.choose"
    bl_label = "Choose Theme"
    mode: EnumProperty(items=[('LIGHT', "Light", ""), ('DARK', "Dark", "")])
    selection: StringProperty()

    def execute(self, _context):
        prefs = preferences()
        if prefs is None:
            return {'CANCELLED'}
        setattr(prefs, "light_theme" if self.mode == 'LIGHT' else "dark_theme", self.selection)
        return {'FINISHED'}


def draw_theme_menu(layout, mode):
    for selection in (themes.BUILTIN_LIGHT, themes.BUILTIN_DARK):
        op = layout.operator("sts.choose", text=themes.theme_label(selection))
        op.mode, op.selection = mode, selection
    layout.separator()
    try:
        for path, label in themes.installed_themes():
            if bpy.utils.is_path_builtin(path) and path.endswith(("Blender_Light.xml", "Blender_Dark.xml")):
                continue
            op = layout.operator("sts.choose", text=label)
            op.mode, op.selection = mode, path
    except Exception:
        layout.label(text="Could not list installed themes", icon='ERROR')


class STS_MT_light(bpy.types.Menu):
    bl_label = "Light Theme"

    def draw(self, _context):
        draw_theme_menu(self.layout, 'LIGHT')


class STS_MT_dark(bpy.types.Menu):
    bl_label = "Dark Theme"

    def draw(self, _context):
        draw_theme_menu(self.layout, 'DARK')


class STS_OT_sync(bpy.types.Operator):
    bl_idname = "sts.sync"
    bl_label = "Sync Now"
    bl_description = "Read macOS appearance again and reapply the chosen theme"

    def execute(self, context):
        changed(None, context)
        return {'FINISHED'}


class STS_OT_restore(bpy.types.Operator):
    bl_idname = "sts.restore"
    bl_label = "Restore Previous Theme"
    bl_description = "Pause automatic switching and restore the theme before this session's first switch"

    def execute(self, _context):
        global _original, _applied, _status
        if _original is None:
            return {'CANCELLED'}
        try:
            transition.stop()
            themes.restore_theme(_original)
        except Exception as exc:
            self.report({'ERROR'}, str(exc))
            return {'CANCELLED'}
        preferences().enabled = False
        _probe.close()
        _original, _applied = None, None
        _status = "Restored previous theme — automatic switching paused"
        return {'FINISHED'}


_CLASSES = (STS_Preferences, STS_OT_choose, STS_MT_light, STS_MT_dark, STS_OT_sync, STS_OT_restore)


@persistent
def before_load(_dummy):
    # Finish while RNA references are still valid; no cached references cross a load.
    transition.stop(finish=True)


def register():
    global _original, _applied, _status, _force, _next_poll
    _original, _applied = None, None
    _status = "Waiting for macOS appearance"
    _force, _next_poll = True, 0.0
    for cls in _CLASSES:
        bpy.utils.register_class(cls)
    bpy.app.timers.register(tick, first_interval=1.0, persistent=True)
    bpy.app.handlers.load_pre.append(before_load)


def unregister():
    global _original, _applied
    if bpy.app.timers.is_registered(tick):
        bpy.app.timers.unregister(tick)
    _probe.close()
    transition.stop(finish=True)
    if before_load in bpy.app.handlers.load_pre:
        bpy.app.handlers.load_pre.remove(before_load)
    for cls in reversed(_CLASSES):
        bpy.utils.unregister_class(cls)
    _original, _applied = None, None
