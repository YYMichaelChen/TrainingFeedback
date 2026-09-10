"""验收数据准备入口回归：合成根包含打包验收所需的全部场景且只落在临时目录。"""

import importlib.util
import json
from pathlib import Path

import pytest
from PySide6.QtGui import QImage

from training_feedback.app import ApplicationContext
from training_feedback.data.data_root import open_existing
from training_feedback.data.locator import Locator


def _load_fixture_module():
    spec = importlib.util.spec_from_file_location(
        "prepare_acceptance_data",
        Path(__file__).resolve().parents[1] / "packaging" / "prepare_acceptance_data.py",
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def fixture_result(tmp_path):
    module = _load_fixture_module()
    return module.prepare_acceptance_root(tmp_path / "fixture")


def test_fixture_root_covers_packaged_acceptance_scenarios(fixture_result):
    root = open_existing(fixture_result["data_root"])
    context = ApplicationContext.reopen(
        root.path, Locator(fixture_result["base"] / "reopen" / "locator.json")
    )
    try:
        connection = context.database.connection
        sessions = context.session_repository()

        # 计划：一个被取代版本 + 一个启用版本，导入草稿保持 draft。
        plans = context.plan_repository().get_plan(
            next(
                plan["id"]
                for plan in context.plan_repository().list_plans()
                if plan["name"].startswith("【合成验收数据】验收演示计划")
            )
        )
        statuses = [revision["status"] for revision in plans["revisions"]]
        assert statuses.count("superseded") == 1
        assert statuses.count("active") == 1
        assert statuses.count("draft") == 1  # 导入草稿未被激活

        # 会话：完成、部分完成、可恢复的暂停各一。
        completed = sessions.get(fixture_result["sessions"]["completed"])
        partial = sessions.get(fixture_result["sessions"]["partial"])
        assert completed["status"] == "completed"
        assert partial["status"] == "partial"
        active = sessions.get_active()
        assert active["id"] == fixture_result["sessions"]["paused"]
        assert active["status"] == "paused"

        # 超额结果带实际组，备注逐字保留；未完成不含实际剂量。
        exceeded = next(a for a in completed["actions"] if a["result"] == "exceeded")
        assert exceeded["note"] == "【合成验收数据】  超额完成\t保留原文  "
        assert [s["value"] for s in exceeded["actual_sets"]] == [14, 14]
        not_completed = next(a for a in partial["actions"] if a["result"] == "not_completed")
        assert not_completed["actual_sets"] == []

        # 次日反馈：含显式未答（未知）区域。
        feedback = context.feedback_repository().get(partial["id"])
        values = {area["body_area_name_snapshot"]: area["value"] for area in feedback["areas"]}
        assert values["臀部"] == "significant_soreness"
        assert values["大腿前侧"] is None

        # 导出登记 JSON+Markdown 且文件存在；导入草稿留档。
        exports = connection.execute("SELECT format FROM ai_export ORDER BY id").fetchall()
        assert [row[0] for row in exports] == ["json", "markdown"]
        assert len(list((root.path / "exports").glob("*"))) == 2
        imports = connection.execute("SELECT status, rationale FROM plan_import").fetchall()
        assert len(imports) == 1 and imports[0][0] == "draft_created"
        assert "合成验收数据" in imports[0][1]
        assert len(list((root.path / "imports").glob("*.json"))) == 1

        # 可解码的合成图片与隔离 locator。
        image_paths = sorted((root.path / "exercise-images").glob("*.png"))
        assert len(image_paths) == 2
        assert all("合成验收数据" in path.name for path in image_paths)
        decoded = [QImage(str(path)) for path in image_paths]
        assert all(not image.isNull() for image in decoded)
        assert [(image.width(), image.height()) for image in decoded] == [(64, 48), (64, 48)]
        assert image_paths[0].read_bytes() != image_paths[1].read_bytes()
        locator_payload = json.loads(fixture_result["locator"].read_text(encoding="utf-8"))
        assert Path(locator_payload["data_root"]) == fixture_result["data_root"]
    finally:
        context.close()


def test_fixture_refuses_non_empty_base(tmp_path):
    base = tmp_path / "occupied"
    base.mkdir()
    (base / "existing.txt").write_text("do not touch", encoding="utf-8")

    module = _load_fixture_module()
    with pytest.raises(ValueError, match="must be empty"):
        module.prepare_acceptance_root(base)

    assert (base / "existing.txt").read_text(encoding="utf-8") == "do not touch"


def test_fixture_resolves_relative_base_for_cwd_independent_locator(tmp_path, monkeypatch):
    working = tmp_path / "working"
    working.mkdir()
    monkeypatch.chdir(working)
    module = _load_fixture_module()

    result = module.prepare_acceptance_root(Path("relative fixture"))

    expected_base = (working / "relative fixture").resolve()
    assert result["base"] == expected_base
    assert result["data_root"] == expected_base / "data-root"
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    monkeypatch.chdir(elsewhere)
    saved_root = Locator(result["locator"]).load()
    assert saved_root == expected_base / "data-root"
    assert open_existing(saved_root).path == expected_base / "data-root"


def test_fixture_marks_everything_synthetic(fixture_result):
    notice = (fixture_result["base"] / "README.txt").read_text(encoding="utf-8")
    assert "合成" in notice
    assert "LOCALAPPDATA" in notice
    root = open_existing(fixture_result["data_root"])
    context = ApplicationContext.reopen(
        root.path, Locator(fixture_result["base"] / "reopen2" / "locator.json")
    )
    try:
        plans = context.plan_repository().list_plans()
        names = [plan["name"] for plan in plans]
        assert "臀腿与核心基础" in names  # 种子提案保持原样
        fixture_plans = [name for name in names if name != "臀腿与核心基础"]
        assert len(fixture_plans) == 1
        assert fixture_plans[0].startswith("【合成验收数据】")
    finally:
        context.close()
