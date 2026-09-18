# Verification — 0.1.3

Version set to 0.1.3 at the user’s explicit request. This package includes event-driven detection and fixed 0.35-second transitions.

- 85 checks passed: 14 Python tests (including 6 actual macOS distributed-notification tests), 26 Blender integration checks, 25 transition checks, and 20 notification integration checks.
- A private test notification name prevents test traffic from affecting other apps or the user's active theme switcher.
- Native tests verify main-thread callback delivery, duplicate registration prevention, unsubscription, reopening, and idle silence.
- Blender checks verify one startup read, zero recurring timer/child process at rest, no reads beyond the old polling interval, notification-triggered reads, burst coalescing, follow-up reads when events arrive during an outstanding query, pause/resume cleanup, visible read failures, event-based recovery, and disable cleanup.
- A separate factory-startup Blender GUI process passed an actual run-loop smoke test: one initial query, no idle query, a native test notification, one additional query, completed transition, no remaining detection timer, and released observer on disable. The process then exited.
- Existing unit and transition regressions passed. OS settings were not toggled; actual appearance-change notification delivery remains a manual end-to-end check. The appearance notification name is de facto, not an Apple-guaranteed constant.
- Blender extension build and ZIP validation passed for `system_theme_switcher-0.1.3.zip`; archive contents include the native observer and fixed-duration transition, with no Python caches.
- Version changed to 0.1.3 as requested; no tags were created. Prior package checks below are historical.

## Prior verification

# Verification — 0.2.0

Tested on Blender 5.0.1, macOS Sequoia 15.7.4, arm64.

- 59 checks passed: 8 appearance unit tests, 26 Blender integration checks, and 25 transition checks. The transition effect toggle and duration preference have been removed; all switches use a fixed 0.35 seconds.
- Transition checks exercise actual theme RNA: source preservation at start, interpolated midpoint, reversal from current colors, exact final colors and font settings, failed replacement, pause, restore, file loading, disable cleanup, and original backup preservation.
- 21 color update steps took about 41 ms total in a background Blender process. This measures property updates only, not visible GUI rendering or guaranteed frame rate.
- Blender extension ZIP build and validation passed for the earlier 0.2.0 package. The fixed-duration settings change is verified from source; that existing ZIP has not been rebuilt.
- Visible GUI smoothness and live OS-toggle timing have not been visually verified. Native macOS animation API is not used; the add-on interpolates Blender theme colors with smoothstep easing.

## Previous 0.1.0 installation verification


Tested on Blender 5.0.1, macOS Sequoia 15.7.4, arm64.

- 8 Python unit tests passed: appearance parsing, missing-key light mode, unknown/error values, nonblocking polling, subprocess cleanup and timeout, unsupported platforms.
- 26 Blender integration checks passed: registration, preset discovery, built-in light/dark application, custom XML, original theme capture, unchanged-mode behavior, explicit reapplication, changed selection, missing/deleted/malformed XML, rollback after Blender's preset operator fails, exact theme/font restoration, pause, actual host appearance detection, failure status, persistence across opening a `.blend`, unregister cleanup and re-enable.
- Blender's extension manifest validation and ZIP validation passed.
- Built with Blender's extension build command; package contains manifest, three Python modules, and GPL license, with no bytecode caches.
- ZIP installed and enabled through Blender's extension CLI into an isolated profile under `work/blender-test`. A new Blender process successfully loaded `bl_ext.user_default.system_theme_switcher` from that profile and opened the Add-ons preferences without a reported draw error.
- Existing user preferences were not saved or modified by the test processes. The separate GUI test process was terminated after validation.

Limitations: a screenshot of the isolated test window could not be verified because computer-use selected the already-running Blender instance. Actual OS dark/light settings were not changed. Automatic macOS transitions are covered by the real detector plus programmatically exercised Blender transitions, not by a live OS-toggle end-to-end test. Intel hardware was not tested.

The rollback test intentionally triggers an internal Blender XML error before checking restoration. The bundled Blender Light preset also prints warnings for two absent properties in Blender 5.0.1; preset application still completes. These are expected in this environment.
