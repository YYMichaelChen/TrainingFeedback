"""One synthetic schema25 root opening scenario; no client operation."""

import json
import sqlite3
from pathlib import Path

from training_feedback.data.database import Database


def test_schema25_root_open_upgrades_edit_storage(tmp_path):
    path = tmp_path / "synthetic-schema25.sqlite3"
    source = Path("src/training_feedback/data")
    schema = (source / "schema24.sql").read_text(encoding="utf-8")
    edits = (source / "draft_documents.sql").read_text(encoding="utf-8").replace(
        "CHECK(format_version = 2)", "CHECK(format_version = 1)")
    payload = {"schema_version": 4, "plan": {"name": "", "purpose": "", "days": [
        {"order": 1, "items": [{"kind": "action", "item_id": "synthetic.action",
                                "sets": [{"value": "  ", "per_side": True}],
                                "note": "原始\r\n  文字", "_input": {"side_rest": " 休息 "}}]}]}}
    with sqlite3.connect(path) as connection:
        connection.executescript(schema + edits)
        connection.execute("INSERT INTO schema_migration VALUES (25,'synthetic')")
        connection.execute(
            "INSERT INTO plan_edit_document(id,format_version,purpose,payload_json,"
            "created_at,updated_at) VALUES ('draft.synthetic',1,'new',?,'synthetic','synthetic')",
            (json.dumps(payload, ensure_ascii=False),))
    with Database(path) as connection:
        assert connection.execute("SELECT MAX(version) FROM schema_migration").fetchone()[0] == 26
        row = connection.execute("SELECT * FROM plan_edit_document").fetchone()
        assert row["format_version"] == 2
        upgraded = json.loads(row["payload_json"])
        action = upgraded["plan"]["days"][0]["items"][0]
        assert upgraded["schema_version"] == 5
        assert action["execution_mode"] == "separate_sides"
        assert action["alternating_start"] is None
        assert action["sets"] == payload["plan"]["days"][0]["items"][0]["sets"]
        assert action["note"] == "原始\r\n  文字"
        assert action["_input"] == {"side_rest": " 休息 "}
