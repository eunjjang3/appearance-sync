"""Real Blender RNA and timer lifecycle tests for animated themes."""
from pathlib import Path
import sys
import tempfile
import time
import bpy
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import system_theme_switcher as addon
from system_theme_switcher import themes, transition as fade
checks = []
def check(name, condition):
    assert condition, name
    checks.append(name)
    print('PASS:', name)
def finish():
    fade.advance(fade._started + fade.DURATION + 0.01)
    fade.stop()
addon.register()
entry = bpy.context.preferences.addons.new()
entry.module = 'system_theme_switcher'
prefs = entry.preferences
original = themes.capture_theme()
check('transition controls removed', 'smooth_transition' not in prefs.bl_rna.properties and 'transition_duration' not in prefs.bl_rna.properties)
check('transition duration fixed', fade.DURATION == 0.35)
themes.apply_theme(themes.BUILTIN_LIGHT)
light = themes.capture_theme()
themes.restore_theme(original)
addon.sync_mode('LIGHT', prefs)
check('no target flash at start', themes.capture_theme() == original)
check('animation timer registered', bpy.app.timers.is_registered(fade.frame))
check('colors found', len(fade._colors) > 100)
obj, key, start, end = fade._colors[0]
fade.advance(fade._started + fade.DURATION * 0.5)
check('midpoint interpolates real RNA colors', all(abs(v - (a+b)/2) < 1e-5 for v,a,b in zip(getattr(obj,key), start,end)))
check('midpoint differs from endpoints', themes.capture_theme() not in (original, light))
check('non-color settings held until end', bpy.context.preferences.themes[0].filepath == original[0]['filepath'])
mid = themes.capture_theme()
addon.sync_mode('DARK', prefs)
check('reversal starts from visible intermediate colors', themes.capture_theme() == mid)
check('original backup survives reversal', addon._original == original)
finish()
dark = themes.capture_theme()
check('animation completes', not fade.active())
themes.apply_theme(themes.BUILTIN_DARK)
check('completed state exactly equals native preset', themes.capture_theme() == dark)
addon.sync_mode('LIGHT', prefs)
finish()
check('light ends at exact theme including font styles', themes.capture_theme() == light)

addon.sync_mode('DARK', prefs)
fade.advance(fade._started + fade.DURATION * 0.2)
before = themes.capture_theme()
try:
    fade.begin('/missing-theme.xml')
except RuntimeError:
    pass
check('failed replacement preserves visible state', themes.capture_theme() == before)
check('failed replacement retains pending transition', fade.active())
finish()

addon.sync_mode('LIGHT', prefs)
prefs.enabled = False
check('pause completes pending target', themes.capture_theme() == light and not fade.active())
check('pause removes frame timer', not bpy.app.timers.is_registered(fade.frame))
prefs.enabled = True
addon.sync_mode('DARK', prefs)
bpy.ops.sts.restore()
check('restore cancels animation and restores original', themes.capture_theme() == original and not fade.active())
check('restore leaves no animation timer', not bpy.app.timers.is_registered(fade.frame))

prefs.enabled = True
addon.sync_mode('LIGHT', prefs)
with tempfile.TemporaryDirectory() as tmp:
    path = str(Path(tmp) / 'load.blend')
    bpy.ops.wm.save_as_mainfile(filepath=path)
    bpy.ops.wm.open_mainfile(filepath=path)
check('file load finishes animation safely', not fade.active() and themes.capture_theme() == light)
check('poll timer survives file load', bpy.app.timers.is_registered(addon.tick))
addon.sync_mode('DARK', prefs)
start_time = time.perf_counter()
for i in range(21):
    fade.advance(fade._started + fade.DURATION * i / 20)
print('21 frame updates elapsed ms:', round((time.perf_counter() - start_time) * 1000, 2))
check('late frame still ends exactly', themes.capture_theme() == dark)
fade.stop()
addon.sync_mode('LIGHT', prefs)
addon.unregister()
check('disable settles target', themes.capture_theme() == light)
check('disable removes animation and poll timers', not bpy.app.timers.is_registered(fade.frame) and not bpy.app.timers.is_registered(addon.tick))
check('disable removes load handler', addon.before_load not in bpy.app.handlers.load_pre)
bpy.context.preferences.addons.remove(entry)
print(f'ALL {len(checks)} TRANSITION CHECKS PASSED')
