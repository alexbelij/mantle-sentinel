from __future__ import annotations

import subprocess
import sys

from sentinel import __version__
from sentinel.__main__ import main


def test_version_flag(capsys):
    rc = main(["--version"])
    out = capsys.readouterr().out
    assert rc == 0
    assert __version__ in out


def test_version_subprocess():
    res = subprocess.run(
        [sys.executable, "-m", "sentinel", "--version"],
        capture_output=True,
        text=True,
        check=True,
    )
    assert "mantle-sentinel" in res.stdout
