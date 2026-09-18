import importlib.util
from pathlib import Path
import unittest
from unittest.mock import Mock, patch

path = Path(__file__).resolve().parents[1] / "system_theme_switcher" / "appearance.py"
spec = importlib.util.spec_from_file_location("appearance", path)
appearance = importlib.util.module_from_spec(spec)
spec.loader.exec_module(appearance)


class AppearanceTests(unittest.TestCase):
    def test_dark(self):
        self.assertEqual(appearance.parse_defaults(0, "Dark\n", ""), "DARK")

    def test_explicit_light(self):
        self.assertEqual(appearance.parse_defaults(0, "Light\n", ""), "LIGHT")

    def test_missing_key_is_light(self):
        self.assertEqual(appearance.parse_defaults(1, "", (
            "The domain/default pair of (kCFPreferencesAnyApplication, "
            "AppleInterfaceStyle) does not exist"
        )), "LIGHT")

    def test_failures_are_not_light(self):
        for args in [(1, "", "Permission denied"), (0, "", ""), (0, "Auto", ""),
                     (2, "", "AppleInterfaceStyle does not exist")]:
            with self.subTest(args=args), self.assertRaises(RuntimeError):
                appearance.parse_defaults(*args)

    def test_pending_does_not_wait(self):
        probe = appearance.AppearanceProbe()
        process = probe.process = Mock()
        process.poll.return_value = None
        probe.started = appearance.time.monotonic()
        self.assertIsNone(probe.poll())
        process.communicate.assert_not_called()

    def test_timeout_cleans_up(self):
        probe = appearance.AppearanceProbe()
        process = probe.process = Mock()
        process.poll.return_value = None
        probe.started = -100
        with self.assertRaises(RuntimeError):
            probe.poll()
        process.kill.assert_called_once()
        process.communicate.assert_called_once()
        self.assertIsNone(probe.process)

    def test_completed_process_is_reaped(self):
        probe = appearance.AppearanceProbe()
        process = probe.process = Mock()
        process.poll.return_value = process.returncode = 0
        process.communicate.return_value = ("Dark\n", "")
        self.assertEqual(probe.poll(), "DARK")
        self.assertIsNone(probe.process)

    def test_unsupported_os(self):
        with patch.object(appearance.sys, "platform", "linux"):
            with self.assertRaises(RuntimeError):
                appearance.AppearanceProbe().start()


if __name__ == "__main__":
    unittest.main()
