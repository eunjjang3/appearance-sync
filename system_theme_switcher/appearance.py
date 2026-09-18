# SPDX-License-Identifier: GPL-3.0-or-later
"""Nonblocking macOS appearance probe. No Blender calls or worker threads."""
import os
import subprocess
import sys
import time


def parse_defaults(returncode, stdout, stderr):
    if returncode == 0:
        value = stdout.strip().lower()
        if value in {"dark", "light"}:
            return value.upper()
        raise RuntimeError("macOS returned an unknown appearance value")
    # A missing global key is the standard macOS light appearance state.
    # Other command errors must not be interpreted as Light.
    if (returncode == 1 and "AppleInterfaceStyle" in stderr
            and "does not exist" in stderr):
        return "LIGHT"
    raise RuntimeError("Could not read macOS appearance; current theme kept")


class AppearanceProbe:
    def __init__(self):
        self.process = None
        self.started = 0.0

    def start(self):
        if sys.platform != "darwin":
            raise RuntimeError("Automatic appearance detection currently supports macOS only")
        if self.process is not None:
            return
        self.process = subprocess.Popen(
            ["/usr/bin/defaults", "read", "-g", "AppleInterfaceStyle"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
            env={**os.environ, "LC_ALL": "C", "LANG": "C"},
        )
        self.started = time.monotonic()

    def poll(self):
        if self.process is None:
            return None
        if self.process.poll() is None:
            if time.monotonic() - self.started > 2.0:
                self.close()
                raise RuntimeError("macOS appearance detection timed out; current theme kept")
            return None
        process, self.process = self.process, None
        stdout, stderr = process.communicate()
        return parse_defaults(process.returncode, stdout, stderr)

    def close(self):
        if self.process is not None:
            process, self.process = self.process, None
            if process.poll() is None:
                process.kill()
            process.communicate()
