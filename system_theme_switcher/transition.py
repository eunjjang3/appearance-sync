# SPDX-License-Identifier: GPL-3.0-or-later
"""Short main-thread color transitions. No frame handlers or worker threads."""
import time
import bpy
from . import themes

_target = None
_colors = []
_started = 0.0
DURATION = 0.35


def color_bindings(value, before, after):
    bindings = []
    for key, end in after.items():
        start = before[key]
        if isinstance(end, dict):
            bindings.extend(color_bindings(getattr(value, key), start, end))
        elif isinstance(end, list):
            for child, a, b in zip(getattr(value, key), start, end):
                bindings.extend(color_bindings(child, a, b))
        else:
            prop = value.bl_rna.properties[key]
            if prop.subtype in {'COLOR', 'COLOR_GAMMA'} and start != end:
                bindings.append((value, key, start, end))
    return bindings


def active():
    return _target is not None


def stop(*, finish=False):
    global _target, _colors
    target = _target
    _target, _colors = None, []
    if bpy.app.timers.is_registered(frame):
        bpy.app.timers.unregister(frame)
    if finish and target is not None:
        themes.restore_theme(target)


def advance(now):
    """Time-based progress: busy frames skip ahead instead of extending the fade."""
    global _target, _colors
    if _target is None:
        return None
    if now >= _started + DURATION:
        target = _target
        _target, _colors = None, []
        themes.restore_theme(target)
        return None
    t = max(0.0, (now - _started) / DURATION)
    # Smoothstep has zero velocity at both ends.
    weight = t * t * (3.0 - 2.0 * t)
    for value, key, start, end in _colors:
        setattr(value, key, tuple(a + (b - a) * weight for a, b in zip(start, end)))
    themes.redraw()
    return 1.0 / 60.0


def frame():
    try:
        return advance(time.monotonic())
    except Exception as exc:
        # Do not leave a half-applied preset if a theme RNA reference expires.
        stop(finish=True)
        print(f"Appearance Sync: transition interrupted: {exc}")
        return None


def begin(selection):
    global _target, _colors, _started
    # Blender never draws between these synchronous operations. Read the target
    # through its native preset loader, then put the visible source back.
    before = themes.apply_theme(selection)
    try:
        target = themes.capture_theme()
    finally:
        themes.restore_theme(before)
    prefs = bpy.context.preferences
    colors = color_bindings(prefs.themes[0], before[0], target[0])
    colors += color_bindings(prefs.ui_styles[0], before[1], target[1])
    stop()
    if not colors:
        themes.restore_theme(target)
        return before
    _target, _colors = target, colors
    _started = time.monotonic()
    bpy.app.timers.register(frame, first_interval=0.0)
    return before
