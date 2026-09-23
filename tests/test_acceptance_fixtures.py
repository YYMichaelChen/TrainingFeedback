"""冻结验收基线回归：schema-16 合成根覆盖打包验收场景，转换后原件登记可用。"""

import json

from migration_070_fixtures import create_schema16_baseline
from PySide6.QtGui import QImage

from training_feedback.data.catalog_conversion import convert_catalog_root


def test_fixture_root_covers_packaged_acceptance_scenarios(qt_app, tmp_path):
    result = create_schema16_baseline(tmp_path / "fixture")
    root = result["data_root"]
    tables = result["baseline"]["tables"]

    # 计划：被取代版本、启用版本与导入草稿（保持 draft）都在。
    statuses = [row["status"] for row in tables["training_plan_revision"]]
    assert statuses.count("superseded") == 1
    assert statuses.count("active") == 1
    assert statuses.count("draft") == 2  # 初始提案草稿 + 导入草稿

    # 会话：完成、部分完成、可恢复的暂停各一。
    sessions = {row["id"]: row["status"] for row in tables["training_session"]}
    assert sessions == {
        result["sessions"]["completed"]: "completed",
        result["sessions"]["partial"]: "partial",
        result["sessions"]["paused"]: "paused",
    }

    # 超额结果带实际组，备注逐字保留。
    exceeded = next(
        row for row in tables["training_session_action"] if row["result"] == "exceeded"
    )
    assert exceeded["note"] == "【合成验收数据】  超额完成\t保留原文  "
    actual = [
        row["value"]
        for row in tables["training_session_actual_set"]
        if row["session_action_id"] == exceeded["id"]
    ]
    assert actual == [14, 14]

    # 次日反馈：含显式未答（未知）区域。
    values = {
        row["body_area_name_snapshot"]: row["value"]
        for row in tables["next_day_feedback_area"]
    }
    assert values["臀部"] == "significant_soreness"
    assert values["大腿前侧"] is None

    # 导出登记 JSON+Markdown 且文件存在；导入草稿留档；旧运行时的原生路径可解析。
    assert [row["format"] for row in tables["ai_export"]] == ["json", "markdown"]
    assert all("\\" in row["file_path"] for row in tables["ai_export"])
    assert len(list((root / "exports").glob("*"))) == 2
    imports = tables["plan_import"]
    assert len(imports) == 1 and imports[0]["status"] == "draft_created"
    assert "合成验收数据" in imports[0]["rationale"]
    assert len(list((root / "imports").glob("*.json"))) == 1

    # 可解码的合成图片与隔离 locator。
    image_paths = sorted(
        path for path in (root / "exercise-images").glob("*.png")
        if "合成验收数据" in path.name
    )
    assert len(image_paths) == 2
    decoded = [QImage(str(path)) for path in image_paths]
    assert all(not image.isNull() for image in decoded)
    assert [(image.width(), image.height()) for image in decoded] == [(64, 48), (64, 48)]
    assert image_paths[0].read_bytes() != image_paths[1].read_bytes()
    locator_payload = json.loads(result["locator"].read_text(encoding="utf-8"))
    assert locator_payload["data_root"] == str(root)

    # 转换成功且所有旧导入/导出登记都找到原件字节（含 Windows 原生分隔符路径）。
    assert convert_catalog_root(root)
    import sqlite3
    from contextlib import closing

    uri = (root / "training_feedback.sqlite3").as_uri() + "?mode=ro"
    with closing(sqlite3.connect(uri, uri=True)) as db:
        registrations = [
            json.loads(row[1])
            for row in db.execute(
                "SELECT kind, facts_json FROM conversion_registration ORDER BY kind, id"
            )
        ]
    assert [row["available"] for row in registrations] == [True, True, True]
    assert all(row["sha256"] for row in registrations)
