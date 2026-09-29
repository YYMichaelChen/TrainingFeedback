"""Repository documentation governance checks."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def test_documentation_links_paths_and_identities_are_consistent():
    root = Path(__file__).resolve().parents[1]
    result = subprocess.run(
        [sys.executable, "packaging/check_docs.py"],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    assert result.returncode == 0, result.stdout + result.stderr
