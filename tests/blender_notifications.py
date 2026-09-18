"""Real native notification -> one-shot Blender synchronization, without OS changes."""
import ctypes as C
from pathlib import Path
import sys
import time
import uuid
from unittest.mock import patch
import bpy
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import system_theme_switcher as addon
from system_theme_switcher import transition, themes
from system_theme_switcher.notifications import AppearanceObserver

checks = []
def check(name, condition):
    assert condition, name
    checks.append(name)
    print('PASS:', name)

def drain():
    deadline = time.monotonic() + 3
    while True:
        delay = addon.tick()
        if delay is None:
            # In background mode we drive callbacks ourselves. Emulate Blender's
            # removal of callbacks returning None (the real GUI does this itself).
            if bpy.app.timers.is_registered(addon.tick):
                bpy.app.timers.unregister(addon.tick)
            break
        assert time.monotonic() < deadline, 'query did not finish'
        time.sleep(delay)
    if transition.active():
        transition.advance(transition._started + transition.DURATION + .01)
        transition.stop()

addon._observer = AppearanceObserver(addon.request_sync, notification_name='org.sts.test.' + uuid.uuid4().hex)
addon.register()
entry = bpy.context.preferences.addons.new()
entry.module = 'system_theme_switcher'
prefs = entry.preferences
with patch.object(addon._probe, 'start', wraps=addon._probe.start) as starts:
    drain()
    check('startup reads appearance once', starts.call_count == 1)
    check('native observer remains subscribed', addon._observer.active)
    check('no recurring timer after initialization', not bpy.app.timers.is_registered(addon.tick))
    check('no child process left idle', addon._probe.process is None)
    cf = addon._observer._cf
    cf.CFRunLoopRunInMode.argtypes = [C.c_void_p, C.c_double, C.c_bool]
    cf.CFRunLoopRunInMode.restype = C.c_int32
    cf.CFNotificationCenterPostNotification.argtypes = [C.c_void_p]*4 + [C.c_bool]
    cf.CFNotificationCenterPostNotification.restype = None
    run_mode = C.c_void_p.in_dll(cf, 'kCFRunLoopDefaultMode')
    def post():
        cf.CFNotificationCenterPostNotification(addon._observer._center, addon._observer._name, None, None, True)
        cf.CFRunLoopRunInMode(run_mode, .1, False)
    cf.CFRunLoopRunInMode(run_mode, 2.3, False)
    check('idle beyond old polling period performs no reads', starts.call_count == 1)
    check('idle does not schedule timers', not bpy.app.timers.is_registered(addon.tick))
    post()
    check('real distributed notification schedules Blender work', bpy.app.timers.is_registered(addon.tick))
    drain()
    check('notification causes one fresh read', starts.call_count == 2)
    check('notification work returns to idle', not bpy.app.timers.is_registered(addon.tick))
    for _ in range(5):
        post()
    drain()
    check('notification burst coalesces to one read', starts.call_count == 3)

    # Drop stale output if an event arrived while a one-shot read was running.
    applied = addon._applied
    before = themes.capture_theme()
    count_before = starts.call_count
    addon.request_sync()
    with patch.object(addon._probe, 'poll', return_value=None):
        addon.tick()  # Hold the real child's result until a second event arrives.
    addon.request_sync()
    drain()
    check('event during read causes exactly one fresh follow-up', starts.call_count == count_before + 2 and not addon._pending)
    check('same mode does not start an extra transition', addon._applied == applied and themes.capture_theme() == before)

    prefs.enabled = False
    drain()
    check('pause releases native subscription', not addon._observer.active)
    check('pause has no pending timer or child', not bpy.app.timers.is_registered(addon.tick) and addon._probe.process is None)
    prefs.enabled = True
    drain()
    check('resume re-subscribes', addon._observer.active)

    with patch.object(addon._probe, 'start', side_effect=RuntimeError('read failure')):
        addon.request_sync()
        drain()
    check('read failure visible', addon._status.startswith('Error:'))
    check('read failure leaves no polling retry', not bpy.app.timers.is_registered(addon.tick))
    post()
    drain()
    check('new event recovers from read failure', not addon._status.startswith('Error:'))
    addon.unregister()
    check('disable releases observer', not addon._observer.active and addon._observer._callback is None)
    addon.request_sync()
    check('disabled addon cannot be awakened', not bpy.app.timers.is_registered(addon.tick))
bpy.context.preferences.addons.remove(entry)
print(f'ALL {len(checks)} NOTIFICATION INTEGRATION CHECKS PASSED')
