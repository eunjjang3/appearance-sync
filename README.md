# Appearance Sync

**Your themes, in sync with macOS.**

Appearance Sync follows macOS light and dark appearance and smoothly transitions between your chosen Blender themes.

[한국어 안내](README.ko.md)

## Features

- Choose a different installed theme for light and dark mode.
- Follow macOS appearance changes through native notifications, with no periodic system polling.
- Smooth, fixed 0.35-second color transitions, including reversals from the colors currently on screen.
- Use Blender's bundled themes, installed XML presets, or locally installed theme extensions.
- Pause automatic switching, synchronize on demand, or restore the theme from before the session's first switch.
- No network access, additional Python packages, or background worker threads.

## Requirements

Blender **5.0 or newer** on **macOS**. Tested on Blender 5.0.1, macOS Sequoia 15.7.4, Apple Silicon. Intel Macs are included in the package targets but have not been hardware-tested. Windows and Linux are not supported.

## Install

1. In Blender, open **Edit → Preferences → Add-ons → Install from Disk…**.
2. Select `appearance-sync-0.1.3.zip` without extracting it.
3. Enable **Appearance Sync** and expand its preferences.
4. Choose your **Light theme** and **Dark theme**. **Follow macOS Appearance** is enabled by default.

If preference auto-save is off, use **Save Preferences** to keep your selections. The add-on never explicitly saves all your preferences.

The display name changed from *System Theme Switcher*. Its extension ID remains `system_theme_switcher` so existing settings can be retained when updating in the same repository. Do not enable separate copies from different repositories at the same time.

The official Blender Extensions listing has not been published yet. Disk installations do not receive remote repository updates.

## Controls

| Control | Behavior |
| --- | --- |
| Follow macOS Appearance | Enable or pause automatic switching |
| Light theme / Dark theme | Choose an installed preset for each system mode |
| Sync Now | Read the current system appearance and reapply the selected theme |
| Restore Previous Theme | Restore the theme before this session's first switch and pause synchronization |

Color transitions always take **0.35 seconds**. Fonts, sizes, and other non-color settings are applied at the end. Pausing or disabling during a transition completes the target theme; Restore cancels the transition and restores the original snapshot.

## Behavior and limitations

- Applies the **entire selected theme**, including viewport colors and font styles defined in the preset.
- Reads macOS appearance once at startup and again after a notification or explicit settings change. No detection timer remains active while idle; short-lived timers handle an outstanding read and the color transition.
- Uses CoreFoundation's distributed notification center and the de facto `AppleInterfaceThemeChangedNotification` name. That name is not an Apple-guaranteed public constant. Use **Sync Now** if a notification is missed.
- The original theme snapshot is kept only for the current add-on session. Export important custom themes separately before relying on session restoration.
- Custom presets are stored as absolute paths. Reselect them after moving files or migrating to another computer. Editing a preset file requires **Sync Now** to reload it.
- Missing presets or failed appearance reads preserve the current theme and show an error. A new notification or **Sync Now** retries the operation.

## Development

```sh
python3 -m unittest discover -s tests -p 'test_*.py' -v
blender --background --factory-startup --python-exit-code 1 --python tests/blender_integration.py
blender --background --factory-startup --python-exit-code 1 --python tests/blender_transition.py
blender --background --factory-startup --python-exit-code 1 --python tests/blender_notifications.py
blender --background --factory-startup --command extension validate system_theme_switcher
blender --background --factory-startup --command extension build --source-dir system_theme_switcher --output-filepath appearance-sync-0.1.3.zip
```

Blender must be on your PATH, or substitute its full executable path. Native notification tests require macOS. Tests use private notification names; they do not toggle the system appearance. The rollback test intentionally produces a Blender XML error before verifying recovery.

See [verification notes](VERIFICATION.md) for automated checks and their limits. The user has also reported successful real-system appearance switching.

## Support and license

Report reproducible issues with your Blender version, macOS version, selected themes, and the status shown in preferences at [GitHub Issues](https://github.com/eunjjang3/appearance-sync/issues).

[GPL-3.0-or-later](LICENSE).
