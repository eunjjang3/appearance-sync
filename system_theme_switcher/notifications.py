# SPDX-License-Identifier: GPL-3.0-or-later
"""Subscribe to macOS appearance changes without polling or extra packages.

The distributed center is public CoreFoundation API. The appearance notification
name is de facto (also used by Electron), not an Apple-guaranteed public constant.
Register/remove on the main thread; Cocoa delivers through its main run loop.
"""
import ctypes as C
import sys
import threading

APPEARANCE_CHANGED = "AppleInterfaceThemeChangedNotification"
_CALLBACK = C.CFUNCTYPE(None, C.c_void_p, C.c_void_p, C.c_void_p, C.c_void_p, C.c_void_p)


class AppearanceObserver:
    def __init__(self, on_change, *, notification_name=APPEARANCE_CHANGED):
        self.on_change = on_change
        self.notification_name = notification_name
        self._cf = None
        self._center = None
        self._name = None
        self._callback = None
        self.active = False

    @staticmethod
    def _require_main_thread():
        if threading.current_thread() is not threading.main_thread():
            raise RuntimeError("Appearance notifications must run on Blender's main thread")

    def start(self):
        self._require_main_thread()
        if self.active:
            return
        if sys.platform != "darwin":
            raise RuntimeError("Automatic appearance detection currently supports macOS only")
        cf = C.CDLL('/System/Library/Frameworks/CoreFoundation.framework/CoreFoundation')
        cf.CFNotificationCenterGetDistributedCenter.argtypes = []
        cf.CFNotificationCenterGetDistributedCenter.restype = C.c_void_p
        cf.CFStringCreateWithCString.argtypes = [C.c_void_p, C.c_char_p, C.c_uint32]
        cf.CFStringCreateWithCString.restype = C.c_void_p
        cf.CFNotificationCenterAddObserver.argtypes = [
            C.c_void_p, C.c_void_p, _CALLBACK, C.c_void_p, C.c_void_p, C.c_long,
        ]
        cf.CFNotificationCenterAddObserver.restype = None
        cf.CFNotificationCenterRemoveObserver.argtypes = [C.c_void_p] * 4
        cf.CFNotificationCenterRemoveObserver.restype = None
        cf.CFRelease.argtypes = [C.c_void_p]
        cf.CFRelease.restype = None
        center = cf.CFNotificationCenterGetDistributedCenter()
        name = cf.CFStringCreateWithCString(None, self.notification_name.encode(), 0x08000100)
        if not center or not name:
            if name:
                cf.CFRelease(name)
            raise RuntimeError("Could not subscribe to macOS appearance notifications")

        @_CALLBACK
        def receive(_center, _observer, _name, _object, _info):
            # Ignore payloads entirely; a notification only requests a fresh OS read.
            try:
                self._require_main_thread()
                if self.active:
                    self.on_change()
            except Exception as exc:
                # Never let a Python exception unwind through a native callback.
                print(f"Appearance Sync: notification callback failed: {exc}")

        self._cf, self._center, self._name, self._callback = cf, center, name, receive
        try:
            cf.CFNotificationCenterAddObserver(center, id(self), receive, name, None, 4)
            self.active = True
        except Exception:
            cf.CFRelease(name)
            self._cf = self._center = self._name = self._callback = None
            raise

    def close(self):
        self._require_main_thread()
        if not self.active:
            return
        self.active = False
        # Remove before releasing either the CFString or the Python C callback.
        self._cf.CFNotificationCenterRemoveObserver(self._center, id(self), self._name, None)
        self._cf.CFRelease(self._name)
        self._cf = self._center = self._name = self._callback = None
