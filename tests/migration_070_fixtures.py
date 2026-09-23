"""Frozen synthetic schema-16 preservation baseline for the catalog conversion.

The baseline bytes live in docs/contracts/baseline/ (schema16-root/,
schema16-preservation.json, schema16-fixture.json). They were generated once with
the pre-retirement 0.6.1 working-tree runtime as a synthetic stand-in; the
generating code retired with the old desktop runtime in 070-G3. The fixture is
not a claim that it came from the preserved packaged 0.6.1 binary.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import sqlite3
from contextlib import closing
from pathlib import Path

from training_feedback.data.locator import Locator

FIXTURES = Path(__file__).resolve().parents[1] / "docs" / "contracts" / "baseline"


def logical_baseline(root: Path) -> dict:
    """Read only the explicitly supplied synthetic root; never run migrations here."""
    uri = (root / "training_feedback.sqlite3").as_uri() + "?mode=ro"
    with closing(sqlite3.connect(uri, uri=True)) as db:
        db.row_factory = sqlite3.Row
        tables = [row[0] for row in db.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' "
            "ORDER BY name"
        )]
        records = {}
        for table in tables:
            quoted = '"' + table.replace('"', '""') + '"'
            records[table] = sorted(
                (dict(row) for row in db.execute(f"SELECT * FROM {quoted}")),
                key=lambda row: json.dumps(row, sort_keys=True, ensure_ascii=False),
            )
        assert db.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        assert db.execute("PRAGMA foreign_key_check").fetchall() == []
    resources = {
        path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(root.rglob("*"))
        if path.is_file() and not path.name.startswith("training_feedback.sqlite3")
    }
    return {"tables": records, "resources": resources}


def create_schema16_baseline(base: Path) -> dict:
    """Materialize the frozen schema-16 baseline into a temp directory.

    Returns the same logical shape the retired generator produced: the copied
    data root, a fresh locator pointing at it, recorded session identities and
    the preserved logical facts. The checked-in fixture itself stays untouched.
    """
    base = Path(base)
    base.mkdir(parents=True, exist_ok=True)
    root = base / "data-root"
    shutil.copytree(FIXTURES / "schema16-root", root)
    preservation = json.loads(
        (FIXTURES / "schema16-preservation.json").read_text(encoding="utf-8")
    )
    metadata = json.loads((FIXTURES / "schema16-fixture.json").read_text(encoding="utf-8"))
    locator = base / "locator.json"
    Locator(locator).save(root)
    return {
        "base": base,
        "data_root": root,
        "locator": locator,
        "sessions": metadata["sessions"],
        "exports": metadata["exports"],
        "mapping_expectations": metadata["mapping_expectations"],
        "baseline": {"tables": preservation["tables"], "resources": preservation["resources"]},
    }
