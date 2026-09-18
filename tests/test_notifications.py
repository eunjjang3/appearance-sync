"""Exercise the actual macOS distributed center using a private test event name."""
import ctypes as C
import importlib.util
from pathlib import Path
import sys
import threading
import unittest
import uuid

path = Path(__file__).resolve().parents[1] / 'system_theme_switcher' / 'notifications.py'
spec = importlib.util.spec_from_file_location('notifications', path)
notifications = importlib.util.module_from_spec(spec)
spec.loader.exec_module(notifications)

@unittest.skipUnless(sys.platform == 'darwin', 'macOS native notification tests')
class NotificationTests(unittest.TestCase):
    def setUp(self):
        self.events = []
        self.observer = notifications.AppearanceObserver(
            lambda: self.events.append(threading.current_thread()),
            notification_name='org.system-theme-switcher.test.' + uuid.uuid4().hex,
        )
        self.observer.start()
        self.cf = self.observer._cf
        self.cf.CFNotificationCenterPostNotification.argtypes = [C.c_void_p]*4 + [C.c_bool]
        self.cf.CFNotificationCenterPostNotification.restype = None
        self.cf.CFRunLoopRunInMode.argtypes = [C.c_void_p, C.c_double, C.c_bool]
        self.cf.CFRunLoopRunInMode.restype = C.c_int32
        self.mode = C.c_void_p.in_dll(self.cf, 'kCFRunLoopDefaultMode')
        self.name = self.cf.CFStringCreateWithCString(None, self.observer.notification_name.encode(), 0x08000100)
        self.center = self.observer._center

    def tearDown(self):
        self.observer.close()
        self.cf.CFRelease(self.name)

    def post(self):
        self.cf.CFNotificationCenterPostNotification(self.center, self.name, None, None, True)
        self.cf.CFRunLoopRunInMode(self.mode, .2, False)

    def test_native_delivery_on_main_thread(self):
        self.post()
        self.assertEqual(self.events, [threading.main_thread()])

    def test_duplicate_start_does_not_duplicate_delivery(self):
        self.observer.start()
        self.post()
        self.assertEqual(len(self.events), 1)

    def test_close_removes_callback(self):
        self.observer.close()
        self.post()
        self.assertEqual(self.events, [])
        self.assertIsNone(self.observer._callback)
        self.assertIsNone(self.observer._name)

    def test_reopen_after_close(self):
        self.observer.close()
        self.observer.start()
        self.post()
        self.assertEqual(len(self.events), 1)

    def test_idle_does_not_invoke_callback(self):
        self.cf.CFRunLoopRunInMode(self.mode, .2, False)
        self.assertEqual(self.events, [])

    def test_other_thread_cannot_register(self):
        errors = []
        def run():
            try:
                self.observer.start()
            except RuntimeError as exc:
                errors.append(str(exc))
        thread = threading.Thread(target=run)
        thread.start()
        thread.join()
        self.assertEqual(len(errors), 1)

if __name__ == '__main__':
    unittest.main()
