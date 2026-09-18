# SPDX-License-Identifier: GPL-3.0-or-later
"""Theme discovery and transactional application on Blender's main thread."""
from pathlib import Path
import tomllib
import xml.etree.ElementTree as ET

import bpy

BUILTIN_LIGHT = "builtin:light"
BUILTIN_DARK = "builtin:dark"


def installed_themes():
    """Include legacy XML presets and locally installed theme extensions."""
    found = {}
    for directory in bpy.utils.preset_paths("interface_theme"):
        for path in sorted(Path(directory).glob("*.xml")):
            found[str(path.resolve())] = path.stem.replace("_", " ")
    for repo in bpy.context.preferences.extensions.repos:
        if not repo.enabled or not repo.directory:
            continue
        for manifest in sorted(Path(repo.directory).glob("*/blender_manifest.toml")):
            try:
                data = tomllib.loads(manifest.read_text(encoding="utf-8"))
                if data.get("type") != "theme":
                    continue
                for path in sorted(manifest.parent.glob("*.xml")):
                    found[str(path.resolve())] = (
                        f"{data.get('name', manifest.parent.name)} / {path.stem}"
                    )
            except (OSError, ValueError):
                continue
    return sorted(found.items(), key=lambda pair: (pair[1].casefold(), pair[0]))


def resolve_theme(selection):
    if selection in {BUILTIN_LIGHT, BUILTIN_DARK}:
        filename = "Blender_Light.xml" if selection == BUILTIN_LIGHT else "Blender_Dark.xml"
        # Use the bundled copy, so an identically named user theme cannot override it.
        for root in bpy.utils.script_paths():
            path = Path(root) / "presets" / "interface_theme" / filename
            if path.is_file() and bpy.utils.is_path_builtin(str(path)):
                return path
        raise RuntimeError(f"Bundled theme not found: {filename}")
    path = Path(selection)
    if path.suffix.lower() != ".xml" or not path.is_file():
        raise RuntimeError("Selected theme is missing; choose an installed theme again")
    return path


def theme_label(selection):
    if selection == BUILTIN_LIGHT:
        return "Blender Light"
    if selection == BUILTIN_DARK:
        return "Blender Dark"
    return Path(selection).stem.replace("_", " ") or "Choose a theme"


def capture_rna(value):
    result = {}
    for prop in value.bl_rna.properties:
        key = prop.identifier
        if key == "rna_type":
            continue
        item = getattr(value, key)
        if prop.type == "POINTER":
            if item is not None:
                result[key] = capture_rna(item)
        elif prop.type == "COLLECTION":
            result[key] = [capture_rna(child) for child in item]
        elif not prop.is_readonly:
            result[key] = tuple(item) if getattr(prop, "is_array", False) else item
    return result


def restore_rna(value, snapshot):
    for key, item in snapshot.items():
        if isinstance(item, dict):
            restore_rna(getattr(value, key), item)
        elif isinstance(item, list):
            for child, saved in zip(getattr(value, key), item):
                restore_rna(child, saved)
        else:
            setattr(value, key, item)


def capture_theme():
    prefs = bpy.context.preferences
    return (capture_rna(prefs.themes[0]), capture_rna(prefs.ui_styles[0]))


def restore_theme(snapshot):
    prefs = bpy.context.preferences
    restore_rna(prefs.themes[0], snapshot[0])
    restore_rna(prefs.ui_styles[0], snapshot[1])
    redraw()


def redraw():
    for wm in bpy.data.window_managers:
        for window in wm.windows:
            for area in window.screen.areas:
                area.tag_redraw()


def apply_theme(selection):
    path = resolve_theme(selection)
    # Validate before Blender's preset operator resets the theme.
    root = ET.parse(path).getroot()
    if (root.tag != "bpy" or root.find("Theme") is None
            or any(child.tag not in {"Theme", "ThemeStyle"} for child in root)):
        raise RuntimeError("This XML file is not a Blender theme preset")
    before = capture_theme()
    try:
        result = bpy.ops.script.execute_preset(
            filepath=str(path), menu_idname="USERPREF_MT_interface_theme_presets",
        )
        if result != {'FINISHED'}:
            raise RuntimeError("Blender could not apply the selected theme")
    except Exception:
        restore_theme(before)
        raise
    redraw()
    return before
