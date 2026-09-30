"""Measurement tooling must stay within owned paths and the tracked inventory."""

import importlib.util
from pathlib import Path

import pytest

SPEC = importlib.util.spec_from_file_location(
    "baseline_measurement", Path(__file__).resolve().parents[1] / "packaging/measure_baseline.py",
)
baseline = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(baseline)


@pytest.mark.parametrize("relative", ["../outside", "child/../../outside"])
def test_measurement_refuses_path_escape(tmp_path, relative):
    owned = tmp_path / "owned"
    owned.mkdir()
    outside = tmp_path / "outside"
    outside.write_text("untouched", encoding="utf-8")
    with pytest.raises(ValueError, match="outside|resolve"):
        baseline.checked_path(owned, relative)
    assert outside.read_text(encoding="utf-8") == "untouched"


def test_measurement_refuses_junction_before_reading(tmp_path, monkeypatch):
    # Simulate Windows junction metadata without requiring symlink creation privileges.
    junction = tmp_path / "redirect"
    monkeypatch.setattr(Path, "is_junction", lambda path: path == junction)
    with pytest.raises(ValueError, match="links or junctions"):
        baseline.checked_path(tmp_path, "redirect/database")
    assert not junction.exists()


def test_inventory_never_enumerates_untracked_roots(tmp_path, monkeypatch):
    source = tmp_path / "src"
    source.mkdir()
    (source / "a.py").write_bytes(b"owned source")
    (source / "b.py").write_bytes(b"owned source")
    protected = tmp_path / "user_data"
    protected.mkdir()
    (protected / "private.sqlite3").write_bytes(b"must never read")
    original = Path.read_bytes

    def read(path):
        assert protected not in path.parents
        return original(path)

    monkeypatch.setattr(baseline, "PROJECT", tmp_path)
    monkeypatch.setattr(baseline, "git", lambda *args: "src/a.py\0src/b.py\0")
    monkeypatch.setattr(Path, "read_bytes", read)
    monkeypatch.setattr(Path, "rglob", lambda *_: pytest.fail("Recursive inventory is forbidden"))
    result = baseline.inventory()
    assert result["total_files"] == 2
    assert result["total_bytes"] == 24
    assert result["exact_duplicates"] == [{"bytes_each": 12, "paths": ["src/a.py", "src/b.py"]}]
