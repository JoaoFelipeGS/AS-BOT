import os
import sys
import unittest
from unittest.mock import patch

from backend.browser_manager import _should_run_headless
from backend.config import settings


class BrowserHeadlessSelectionTests(unittest.TestCase):
    def test_forces_headless_on_linux_without_display_server(self):
        with (
            patch.object(settings, "browser_headless", False),
            patch.object(sys, "platform", "linux"),
            patch.dict(os.environ, {}, clear=True),
        ):
            self.assertTrue(_should_run_headless())

    def test_keeps_headed_mode_on_linux_with_display_server(self):
        with (
            patch.object(settings, "browser_headless", False),
            patch.object(sys, "platform", "linux"),
            patch.dict(os.environ, {"DISPLAY": ":0"}, clear=True),
        ):
            self.assertFalse(_should_run_headless())

    def test_honors_explicit_headless_setting_on_desktop(self):
        with (
            patch.object(settings, "browser_headless", True),
            patch.object(sys, "platform", "win32"),
            patch.dict(os.environ, {}, clear=True),
        ):
            self.assertTrue(_should_run_headless())

    def test_preserves_headed_default_on_windows(self):
        with (
            patch.object(settings, "browser_headless", False),
            patch.object(sys, "platform", "win32"),
            patch.dict(os.environ, {}, clear=True),
        ):
            self.assertFalse(_should_run_headless())


if __name__ == "__main__":
    unittest.main()
