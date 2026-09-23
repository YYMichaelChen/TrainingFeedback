"""Catalog ownership, per-root overlays and immutable resource retention (070-B)."""

from __future__ import annotations

import hashlib
import json
import shutil
import sqlite3
from copy import deepcopy

import pytest
from image_fixtures import png_bytes
from migration_070_fixtures import create_schema16_baseline, logical_baseline

from training_feedback.app import LibraryContext
from training_feedback.data.catalog_builder import build_catalog, source_content
from training_feedback.data.catalog_repository import CatalogRepository
from training_feedback.data.catalog_resources import CatalogError, catalog_directory
from training_feedback.data.data_root import DataRootError
from training_feedback.data.database import Database, transaction
from training_feedback.data.library_images import inspect_images
from training_feedback.data.library_repository import LibraryRepository
from training_feedback.data.seed.images import bundled_image_assets
from training_feedback.domain.catalog import ExerciseReference, content_sha256

BRIDGE = ExerciseReference("bundled", "launch.glute-bridge")
ASSET = png_bytes()
ASSET_HASH = hashlib.sha256(ASSET).hexdigest()


def hashes(directory):
    return {path.relative_to(directory).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in directory.rglob("*") if path.is_file()}


@pytest.fixture
def illustrated_catalog(tmp_path):
    entries = source_content()
    assets = bundled_image_assets()
    assets.pop(entries[0]["content"]["guidance"]["images"][0]["path"])
    entries[0]["content"]["guidance"]["images"] = [{
        "path": "images/synthetic.bin", "sha256": ASSET_HASH, "required": True,
        "status": "available", "caption": "【合成】非真实插图",
    }]
    entries[0]["sha256"] = content_sha256(entries[0]["content"])
    return build_catalog(tmp_path / "只读程序 program/catalog", entries=entries,
                         assets={**assets, "images/synthetic.bin": ASSET})


def test_program_catalog_is_reproducible_readonly_and_cwd_independent(tmp_path, monkeypatch):
    built = build_catalog(tmp_path / "构建 catalog")
    before = hashes(built)
    assert before == hashes(catalog_directory())
    unrelated = tmp_path / "elsewhere"
    unrelated.mkdir()
    monkeypatch.chdir(unrelated)
    with CatalogRepository() as source, CatalogRepository(built) as copied:
        assert source.list() == copied.list()
        assert copied.version == "070-illustrated-2"
        assert len(copied.list()) == 36
        assert len(list((built / "images").glob("*.png"))) == 36
        bridge = copied.get("launch.glute-bridge")
        butterfly = copied.get("launch.butterfly-glute-bridge")
        assert bridge["reference"]["version"] == 4
        assert bridge["content"]["aliases"] == ["常规臀桥", "基础臀桥"]
        assert any(
            "顶部保持3秒" in step["text"]
            for step in bridge["content"]["guidance"]["steps"]
        )
        assert butterfly["reference"]["version"] == 4
        assert butterfly["content"]["aliases"] == ["蛙式臀桥"]
        assert all(
            check.valid
            for entry in copied.list()
            for check in inspect_images(entry["content"]["guidance"]["images"], copied.image_bytes)
        )
        with pytest.raises(sqlite3.OperationalError, match="readonly"):
            copied.connection.execute("DELETE FROM catalog_exercise")
    assert hashes(built) == before
    assert not list(built.rglob("*-journal"))
    assert not list(built.rglob("*-wal"))


@pytest.mark.parametrize("failure", ["database", "image", "manifest"])
def test_catalog_integrity_failure_does_not_touch_user_root(illustrated_catalog, tmp_path, failure):
    if failure == "database":
        (illustrated_catalog / "catalog.sqlite3").write_bytes(b"broken")
    elif failure == "image":
        (illustrated_catalog / "images/synthetic.bin").write_bytes(b"changed")
    else:
        (illustrated_catalog / "catalog-manifest.json").write_text("{}", encoding="utf-8")
    with pytest.raises(CatalogError):
        LibraryContext.create(tmp_path / "must not exist", catalog_path=illustrated_catalog)
    assert not (tmp_path / "must not exist").exists()


def test_new_model_root_has_no_seed_copy_and_no_catalog_write(illustrated_catalog, tmp_path):
    before = hashes(illustrated_catalog)
    with LibraryContext.create(tmp_path / "用户 root", catalog_path=illustrated_catalog) as context:
        assert len(context.library.list()) == 36
        for table in ("exercise", "exercise_guidance_revision", "library_reference",
                      "library_content", "content_snapshot", "training_plan"):
            count = context.database.connection.execute(
                f"SELECT COUNT(*) FROM {table}"
            ).fetchone()[0]
            assert count == 0
        item = context.library.get(BRIDGE)
        assert item["enabled"] is False and item["selected"] is None
        identifier = context.library.retain_bundled(BRIDGE, item["bundled"]["reference"])
        assert context.library.retain_bundled(BRIDGE, item["bundled"]["reference"]) == identifier
        assert context.snapshot_assets.read(ASSET_HASH) == ASSET
        assert context.library.get(BRIDGE)["selected"] is None
    assert hashes(illustrated_catalog) == before


def test_overrides_custom_copy_and_catalog_upgrade_keep_originals(illustrated_catalog, tmp_path):
    root = tmp_path / "user"
    with LibraryContext.create(root, catalog_path=illustrated_catalog) as context:
        entry = context.catalog.get(BRIDGE.key)
        override = deepcopy(entry["content"])
        override["canonical_name"] = "【合成】  改名臀桥  "
        override["guidance"]["purpose"] = "【合成】  原文\t\r\n保留  "
        override["guidance"]["review"] = {"reviewed_at": "invented"}
        local = context.library.save_override(BRIDGE, override, entry["reference"])
        saved = context.user_library.content(local)
        assert "review" not in saved["content"]["guidance"]
        assert saved["content"]["guidance"]["purpose"] == override["guidance"]["purpose"]
        custom = context.library.copy_to_custom(BRIDGE, saved["reference"], "【合成】副本")
        copied = context.user_library.content(custom)
        assert copied["content"]["exercise"]["source"] == "custom"
        assert copied["content"]["exercise"]["key"] != BRIDGE.key
        assert context.library.get(ExerciseReference(**copied["content"]["exercise"]))[
            "selected"
        ] is None
        assert context.snapshot_assets.read(ASSET_HASH) == ASSET
        count = context.database.connection.execute(
            "SELECT COUNT(*) FROM snapshot_asset"
        ).fetchone()[0]
        assert count == 1
    replacement = source_content()
    replacement[0]["content"]["canonical_name"] = "【合成】新版目录名"
    replacement[0]["version"] += 1
    replacement[0]["sha256"] = content_sha256(replacement[0]["content"])
    newer = build_catalog(
        tmp_path / "new catalog", entries=replacement,
        assets=bundled_image_assets(), version="test-2",
    )
    shutil.rmtree(illustrated_catalog)
    with LibraryContext.reopen(root, catalog_path=newer) as context:
        assert context.catalog.version == "test-2"
        assert context.user_library.content(local) == saved
        assert context.user_library.content(custom) == copied
        assert context.snapshot_assets.read(ASSET_HASH) == ASSET


def test_context_switch_prepares_target_before_releasing_source(illustrated_catalog, tmp_path):
    with LibraryContext.create(tmp_path / "B", catalog_path=illustrated_catalog):
        pass
    context = LibraryContext.create(tmp_path / "A", catalog_path=illustrated_catalog)
    try:
        identifier = context.library.retain_bundled(
            BRIDGE, context.catalog.get(BRIDGE.key)["reference"],
        )
        assert context.switch(tmp_path / "A") is context
        with pytest.raises((DataRootError, OSError)):
            context.switch(tmp_path / "missing")
        assert context.user_library.content(identifier) is not None
        previous = context
        context = context.switch(tmp_path / "B")
        assert previous.database.connection is None and previous.catalog.connection is None
        assert context.user_library.references() == []
        context = context.switch(tmp_path / "A")
        assert context.user_library.content(identifier) is not None
    finally:
        context.close()


def test_custom_image_copy_rejects_changed_bytes_without_partial_user_state(
    illustrated_catalog, tmp_path,
):
    with LibraryContext.create(tmp_path / "user", catalog_path=illustrated_catalog) as context:
        content = deepcopy(context.catalog.get(BRIDGE.key)["content"])
        content["canonical_name"] = "【合成】独立图片动作"
        content["aliases"] = []
        content["guidance"]["images"][0]["path"] = "custom-exercise-images/user.bin"
        custom_image = context.data_root.path / "custom-exercise-images/user.bin"
        custom_image.write_bytes(b"wrong bytes")
        with pytest.raises(CatalogError, match="hash"):
            context.library.create_custom(content)
        assert context.user_library.references() == []
        custom_image.write_bytes(ASSET)
        identifier = context.library.create_custom(content)
        custom_image.unlink()
        saved = context.user_library.content(identifier)
        digest = saved["assets"]["custom-exercise-images/user.bin"]
        assert context.snapshot_assets.read(digest) == ASSET
        # Corruption of a committed retained asset is reported, never silently overwritten.
        (context.snapshot_assets.root / ASSET_HASH).write_bytes(b"corrupt retained")
        with pytest.raises(CatalogError, match="hash"):
            context.snapshot_assets.read(ASSET_HASH)
        with pytest.raises(CatalogError, match="hash"):
            context.snapshot_assets.publish(ASSET, ASSET_HASH)
        assert context.user_library.content(identifier) == saved


def test_failure_after_asset_publication_rolls_back_and_recovers(illustrated_catalog, tmp_path,
                                                               monkeypatch):
    root = tmp_path / "user"
    with LibraryContext.create(root, catalog_path=illustrated_catalog) as context:
        def fail(*args):
            raise RuntimeError("injected SQL failure")
        monkeypatch.setattr(context.user_library, "retain", fail)
        with pytest.raises(RuntimeError, match="injected"):
            context.library.retain_bundled(BRIDGE, context.catalog.get(BRIDGE.key)["reference"])
        assert context.user_library.references() == []
        assert list((root / "snapshot-assets").iterdir()) == []
        # Simulate process exit after publication and before transaction commit.
        context.snapshot_assets.publish(ASSET, ASSET_HASH)
        (root / "snapshot-assets" / ("stage-" + "a" * 32)).write_bytes(b"partial")
    with LibraryContext.reopen(root, catalog_path=illustrated_catalog) as context:
        assert context.user_library.references() == []
        assert list((root / "snapshot-assets").iterdir()) == []


def test_retained_rows_immutable_and_identity_hash_conflicts_rollback(
    illustrated_catalog, tmp_path,
):
    with LibraryContext.create(tmp_path / "user", catalog_path=illustrated_catalog) as context:
        entry = context.catalog.get(BRIDGE.key)
        identifier = context.library.retain_bundled(BRIDGE, entry["reference"])
        connection = context.database.connection
        for table in (
            "content_snapshot", "library_content", "content_snapshot_asset", "snapshot_asset",
        ):
            with pytest.raises(sqlite3.IntegrityError, match="immutable"):
                with transaction(connection):
                    connection.execute(f"DELETE FROM {table}")
        changed = deepcopy(entry)
        changed["content"]["canonical_name"] = "【合成】冲突"
        changed["reference"]["sha256"] = content_sha256(changed["content"])
        with pytest.raises(CatalogError, match="different bytes"):
            with transaction(connection):
                context.user_library.retain(changed, "bundled", {}, {}, "synthetic")
        assert context.user_library.content(identifier)["reference"] == entry["reference"]
        with pytest.raises(CatalogError, match="name conflict"):
            context.library.resolve(BRIDGE, "另一个动作", entry["reference"])
        with pytest.raises(CatalogError, match="changed"):
            context.library.retain_bundled(BRIDGE, {**entry["reference"], "version": 999})


def test_schema17_only_adds_storage_preserving_schema16_business_facts(tmp_path):
    from training_feedback.data.data_root import inspect_existing
    from training_feedback.data.upgrade_recovery import UpgradeRecovery

    baseline = create_schema16_baseline(tmp_path / "old")
    root = baseline["data_root"]
    original_bytes = (root / "training_feedback.sqlite3").read_bytes()
    inspect_existing(root)
    assert (root / "training_feedback.sqlite3").read_bytes() == original_bytes

    def convert(work, _catalog):
        with Database(work / "training_feedback.sqlite3") as connection:
            assert LibraryRepository(connection).references() == []
            assert connection.execute("PRAGMA foreign_key_check").fetchall() == []

    recovery = UpgradeRecovery(root)
    assert recovery.run("test-schema-chain", convert, lambda work, _: inspect_existing(work))
    assert not recovery.run("test-schema-chain", convert, lambda work, _: inspect_existing(work))
    updated = logical_baseline(root)
    assert {key: value for key, value in updated["resources"].items()
            if not key.startswith("backups/") and not key.startswith(".training-feedback")} == (
                baseline["baseline"]["resources"])
    snapshot = next((root / "backups").glob("upgrade-v1-*/snapshot"))
    assert logical_baseline(snapshot)["tables"] == baseline["baseline"]["tables"]
    assert not (snapshot / "backups").exists()
    assert not (snapshot.parent / "work").exists()
    for table, rows in baseline["baseline"]["tables"].items():
        if table != "schema_migration":
            assert updated["tables"][table] == rows
    with pytest.raises(DataRootError, match="not completed"):
        LibraryContext.reopen(root)


def test_manifest_path_escape_rejected(illustrated_catalog, tmp_path):
    path = illustrated_catalog / "catalog-manifest.json"
    manifest = json.loads(path.read_text(encoding="utf-8"))
    manifest["files"][0]["path"] = "../outside.sqlite3"
    path.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(CatalogError):
        CatalogRepository(illustrated_catalog)
