"""Run with Blender --background --factory-startup --python-exit-code 1 --python FILE."""
from pathlib import Path
import sys
import tempfile
import time

import bpy

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import system_theme_switcher as addon
from system_theme_switcher import themes, transition

checks = []


def check(name, condition):
    assert condition, name
    checks.append(name)
    print("PASS:", name)


def sync_and_finish(mode, prefs):
    addon.sync_mode(mode, prefs)
    if transition.active():
        transition.advance(transition._started + transition.DURATION + 0.01)
        transition.stop()


addon.register()
entry = bpy.context.preferences.addons.new()
entry.module = "system_theme_switcher"
prefs = entry.preferences
initial = themes.capture_theme()
check("timer registered", bpy.app.timers.is_registered(addon.tick))
check("default preset choices", prefs.light_theme == themes.BUILTIN_LIGHT and prefs.dark_theme == themes.BUILTIN_DARK)
check("bundled and installed themes discovered", len(themes.installed_themes()) >= 2)

sync_and_finish("LIGHT", prefs)
light = themes.capture_theme()
check("light changes theme", light != initial)
check("original captured before first switch", addon._original == initial)
sync_and_finish("DARK", prefs)
dark = themes.capture_theme()
check("dark differs from light", dark != light)
check("original retained across switches", addon._original == initial)

# With the same OS mode, do not reload every poll and erase manual theme edits.
ui = bpy.context.preferences.themes[0].user_interface
ui.wcol_regular.inner = (0.1, 0.2, 0.3, 1.0)
edited = themes.capture_theme()
sync_and_finish("DARK", prefs)
check("unchanged mode does not reapply", themes.capture_theme() == edited)
bpy.ops.sts.sync()
sync_and_finish("DARK", prefs)
check("explicit sync reapplies", themes.capture_theme() == dark)

# Changing the preset in the same OS mode must still trigger application.
prefs.dark_theme = themes.BUILTIN_LIGHT
sync_and_finish("DARK", prefs)
check("changing selection applies after transition", themes.capture_theme() == light)

with tempfile.TemporaryDirectory() as directory:
    custom = Path(directory) / "Custom.xml"
    custom.write_text(themes.resolve_theme(themes.BUILTIN_DARK).read_text())
    prefs.dark_theme = str(custom)
    sync_and_finish("DARK", prefs)
    check("custom XML preset applies", bpy.context.preferences.themes[0].filepath == str(custom))
    before_error = themes.capture_theme()
    previous_key = addon._applied
    custom.unlink()
    addon._force = True
    try:
        sync_and_finish("DARK", prefs)
        raise AssertionError("missing theme accepted")
    except RuntimeError:
        pass
    check("missing theme keeps current theme", themes.capture_theme() == before_error)
    check("failed switch does not advance state", addon._applied == previous_key)
    custom.write_text("<bpy><Theme>")
    try:
        themes.apply_theme(str(custom))
        raise AssertionError("malformed XML accepted")
    except Exception as exc:
        if isinstance(exc, AssertionError):
            raise
    check("malformed XML keeps current theme", themes.capture_theme() == before_error)

    # Valid XML with a missing ThemeStyle fails inside Blender after its reset.
    # Exercise that actual failure, not a mocked preset operator.
    custom.write_text("<bpy><Theme/></bpy>")
    try:
        themes.apply_theme(str(custom))
        raise AssertionError("failure swallowed")
    except RuntimeError:
        pass
    check("partial apply failure rolls back", themes.capture_theme() == before_error)

check("restore operator succeeds", bpy.ops.sts.restore() == {'FINISHED'})
check("restore returns exact original theme and fonts", themes.capture_theme() == initial)
check("restore pauses automatic switching", not prefs.enabled)
addon.tick()
check("paused timer leaves theme intact", themes.capture_theme() == initial)

prefs.dark_theme = themes.BUILTIN_DARK
prefs.enabled = True
# Exercise the actual macOS subprocess and Blender timer path, without changing OS settings.
deadline = time.monotonic() + 4.0
while time.monotonic() < deadline:
    addon.tick()
    if addon._applied is not None:
        break
    time.sleep(0.05)
check("actual macOS detection applies theme", addon._applied is not None)
print("DETECTED:", addon._status)

# A detector error should remain visible and preserve the previous theme.
before_error = themes.capture_theme()
addon._next_poll = 0
from unittest.mock import patch
with patch.object(addon._probe, "start", side_effect=RuntimeError("test detection failure")):
    addon.tick()
check("detector failure is visible", addon._status.startswith("Error:"))
check("detector failure preserves theme", themes.capture_theme() == before_error)

with tempfile.TemporaryDirectory() as directory:
    blend = str(Path(directory) / "timer-lifecycle.blend")
    bpy.ops.wm.save_as_mainfile(filepath=blend)
    bpy.ops.wm.open_mainfile(filepath=blend)
    check("timer survives opening a blend file", bpy.app.timers.is_registered(addon.tick))

addon.unregister()
check("timer removed on disable", not bpy.app.timers.is_registered(addon.tick))
check("probe cleaned up on disable", addon._probe.process is None)
bpy.context.preferences.addons.remove(entry)
addon.register()
check("re-enable starts fresh", addon._original is None and addon._applied is None)
addon.unregister()
print(f"ALL {len(checks)} BLENDER INTEGRATION CHECKS PASSED")
