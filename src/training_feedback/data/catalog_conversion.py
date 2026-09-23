"""One-time old TrainingFeedback fact conversion; runtime uses only current repositories."""

from __future__ import annotations

import hashlib
import json
import sqlite3
import uuid
from contextlib import closing
from copy import deepcopy
from datetime import UTC, datetime
from pathlib import Path

from ..domain.catalog import ExerciseReference, content_sha256
from ..domain.exercises import is_reviewed
from ..domain.library_eligibility import assess_eligibility
from .catalog_resources import managed_path
from .conversion_repository import OLD_TABLES, ConversionRepository, encode, rows, source_facts
from .data_root import CONFIG_FILENAME, DATABASE_FILENAME, inspect_existing
from .database import Database, transaction
from .group_plan_repository import GroupPlanRepository
from .group_session_repository import GroupSessionRepository
from .library_images import inspect_images
from .library_repository import LibraryRepository
from .library_root import LIBRARY_MODEL
from .root_lock import JOURNAL_FILENAME
from .snapshot_assets import SnapshotAssets
from .upgrade_recovery import UpgradeRecovery, UpgradeRecoveryError, _inventory

OPERATION = "catalog-model-070-g2"
UNKNOWN_CLASSIFICATION = {
    "family_key": None,
    "variant_role": "standalone",
    "variant_order": 1,
    "parent_exercise_key": None,
    "starting_position_class": "unknown",
}


def _read_connection(root):
    db = sqlite3.connect((Path(root) / DATABASE_FILENAME).resolve().as_uri() + "?mode=ro", uri=True)
    db.row_factory = sqlite3.Row
    return db


def convert_catalog_root(root, *, catalog_path=None, checkpoint=None):
    """Public internal boundary for G3 startup; does not save/change the external locator."""
    root = Path(root)
    recovery = UpgradeRecovery(root, catalog_path=catalog_path, checkpoint=checkpoint)
    if (root / JOURNAL_FILENAME).exists():
        recovery.recover()
    inspect_existing(root)
    config = json.loads((root / CONFIG_FILENAME).read_text(encoding="utf-8"))
    if config.get("library_model") == LIBRARY_MODEL:
        return False
    if "library_model" in config:
        raise UpgradeRecoveryError(
            "Unknown library model; this data root needs a newer application."
        )
    converter = CatalogConverter(checkpoint=checkpoint)
    return recovery.run(OPERATION, converter.convert, validate_catalog_conversion)


class CatalogConverter:
    def __init__(self, *, checkpoint=None):
        self.checkpoint = checkpoint or (lambda _phase: None)

    def convert(self, root, catalog):
        self.root, self.catalog = Path(root), catalog
        self.now = datetime.now(UTC).isoformat()
        with closing(_read_connection(root)) as source:
            original = source_facts(
                source, json.loads((root / CONFIG_FILENAME).read_text(encoding="utf-8"))
            )
        self.namespace = uuid.uuid5(uuid.NAMESPACE_URL, content_sha256(original))
        self.original = original
        original_resources = _inventory(root)["files"]
        with Database(root / DATABASE_FILENAME) as db:
            self.db = db
            self.provenance = ConversionRepository(db)
            self.library = LibraryRepository(db)
            self.assets = SnapshotAssets(root)
            self.plans = GroupPlanRepository(db)
            self.sessions = GroupSessionRepository(db)
            if db.execute("SELECT 1 FROM conversion_run").fetchone():
                raise UpgradeRecoveryError("Conversion marker and configuration disagree.")
            for table in ("library_reference", "group_plan", "group_session"):
                if db.execute(f"SELECT 1 FROM {table}").fetchone():
                    raise UpgradeRecoveryError(
                        "An unmarked root already contains current-model work."
                    )
            self.old = {name: rows(db, name) for name in OLD_TABLES}
            db.execute("PRAGMA foreign_keys=OFF")
            try:
                with transaction(db, immediate=True):
                    self.provenance.archive(original)
                    self._exercises()
                    self.checkpoint("conversion_content")
                    self._plans()
                    self._sessions()
                    self._registrations()
                    self.checkpoint("conversion_facts")
                    self.provenance.retire()
                    manifest = {
                        "counts": {name: len(value) for name, value in original["tables"].items()},
                        "catalog_version": catalog.version,
                        "operation": OPERATION,
                        "resources": {
                            path: value
                            for path, value in original_resources.items()
                            if path not in (DATABASE_FILENAME, CONFIG_FILENAME)
                        },
                    }
                    self.provenance.complete(original, self.now, manifest)
                    if db.execute("PRAGMA foreign_key_check").fetchall():
                        raise UpgradeRecoveryError("Converted references failed validation.")
                    self.checkpoint("conversion_before_commit")
            finally:
                db.execute("PRAGMA foreign_keys=ON")
        self.checkpoint("conversion_committed")
        # Known runtime settings are just the format/application identities. Unknown values
        # survive verbatim in conversion_original and are never read as live settings.
        config = {
            key: original["config"][key]
            for key in ("application", "config_version", "data_format_version")
        }
        config["library_model"] = LIBRARY_MODEL
        (root / CONFIG_FILENAME).write_text(encode(config) + "\n", encoding="utf-8")
        (root / "custom-exercise-images").mkdir(exist_ok=True)

    def _key(self, value):
        return uuid.uuid5(self.namespace, value).hex

    def _related(self, table, field, identifier):
        return [row for row in self.old[table] if row[field] == identifier]

    def _entry(self, exercise, revision, *, historical_name=None, historical_areas=None):
        reference = self.identities[exercise["id"]]
        guidance = deepcopy(json.loads(revision["guidance_json"])) if revision else {}
        original_revision = next(
            (
                row
                for row in self.original["tables"].get("exercise_guidance_revision", [])
                if revision and row["id"] == revision["id"]
            ),
            revision,
        )
        original_guidance = (
            json.loads(original_revision["guidance_json"]) if original_revision else {}
        )
        guidance.pop("review", None)
        inventory, assets = [], {}
        for index, image in enumerate(guidance.get("images", [])):
            declaration = {
                "status": "missing",
                "required": True,
                "path": None,
                "sha256": None,
                "caption": image.get("caption", ""),
            }
            path = image.get("path")
            if path and image.get("status") == "available":
                try:
                    data = managed_path(self.root, path).read_bytes()
                except (OSError, ValueError):
                    pass
                else:
                    digest = hashlib.sha256(data).hexdigest()
                    relative = f"custom-exercise-images/{digest}.image"
                    self.assets.publish(data, digest)
                    # Separate paths for identical illustration declarations are unnecessary;
                    # original order/captions and raw declarations remain provenance.
                    if relative not in assets:
                        declaration.update(status="available", path=relative, sha256=digest)
                        assets[relative] = (digest, len(data))
                    else:
                        relative = f"custom-exercise-images/{digest}-{index}.image"
                        declaration.update(status="available", path=relative, sha256=digest)
                        assets[relative] = (digest, len(data))
            inventory.append(declaration)
        guidance["images"] = inventory
        areas = (
            historical_areas
            if historical_areas is not None
            else [
                [self.area_names[row["body_area_id"]], bool(row["is_primary"])]
                for row in self._related("exercise_body_area", "exercise_id", exercise["id"])
            ]
        )
        bundled = self.catalog.get(reference["key"]) if reference["source"] == "bundled" else None
        content = {
            "exercise": reference,
            "canonical_name": historical_name or exercise["canonical_name"],
            "aliases": [
                row["alias"]
                for row in self._related("exercise_alias", "exercise_id", exercise["id"])
            ],
            "category": exercise["category"],
            "equipment_summary": exercise["equipment_summary"],
            "body_areas": areas,
            "classification": deepcopy(
                bundled["content"]["classification"] if bundled else UNKNOWN_CLASSIFICATION
            ),
            "guidance": guidance,
        }
        if historical_name is not None:
            content.update(
                aliases=[],
                category="",
                equipment_summary="",
                classification=deepcopy(UNKNOWN_CLASSIFICATION),
            )
        token = f"guidance.{revision['id']}" if revision else f"unknown.{exercise['id']}"
        if historical_name is not None:
            token += "." + content_sha256({"name": historical_name, "areas": historical_areas})
        entry = {
            "content": content,
            "reference": {
                "id": "migration." + self._key(token),
                "version": revision["revision_number"] if revision else 1,
                "sha256": content_sha256(content),
            },
        }
        evidence = {
            "kind": "stored_session" if historical_name is not None else "migration_time",
            "original_exercise": exercise,
            "original_revision": original_revision,
            "original_guidance": original_guidance,
            "historical_metadata_recorded": False,
            "historical_image_readiness": None,
            "mapped_at": self.now,
        }
        identifier = self.library.retain(
            entry, "override" if bundled else "custom", evidence, assets, self.now
        )
        return self.library.content(identifier)

    def _exercises(self):
        self.identities, self.contents, self.selected, self.fallback = {}, {}, {}, {}
        self.exercise_rows = {row["id"]: row for row in self.old["exercise"]}
        self.revision_rows = {row["id"]: row for row in self.old["exercise_guidance_revision"]}
        self.area_names = {row["id"]: row["name"] for row in self.old["body_area"]}
        for exercise in self.old["exercise"]:
            key = exercise.get("bundled_exercise_key")
            reference = (
                {"source": "bundled", "key": key}
                if key and self.catalog.get(key)
                else {"source": "custom", "key": self._key(f"exercise.{exercise['id']}")}
            )
            self.identities[exercise["id"]] = reference
            self.db.execute(
                "INSERT INTO library_reference VALUES (?,?,?,?)",
                (exercise["id"], reference["source"], reference["key"], exercise["created_at"]),
            )
            self.db.execute("INSERT INTO library_state(reference_id) VALUES (?)", (exercise["id"],))
            self.provenance.map("exercise", exercise["id"], "exercise", reference)
        for exercise in self.old["exercise"]:
            revisions = self._related("exercise_guidance_revision", "exercise_id", exercise["id"])
            for revision in revisions:
                entry = self._entry(exercise, revision)
                self.contents[revision["id"]] = entry
                self.provenance.map(
                    "exercise_guidance_revision", revision["id"], "content", entry["id"]
                )
                review = json.loads(revision["guidance_json"]).get("review", {})
                if is_reviewed({"review": review}):
                    # No image hashes were recorded by these schemas. Empty bindings retain
                    # the decision without claiming current image-specific approval.
                    self.library.append_review(
                        entry["id"],
                        {
                            "event_type": "approved",
                            "content_sha256": entry["reference"]["sha256"],
                            "image_hashes": [],
                            "reviewer_type": review["reviewer_type"],
                            "review_source": review["review_source"],
                            "reviewed_at": review["reviewed_at"],
                            "confirmed_at": review["user_approved_at"],
                            "note": review.get("review_note", ""),
                            "attachment": self._attachment(review),
                        },
                    )
            selected = self.contents.get(exercise["active_guidance_revision_id"])
            self.fallback[exercise["id"]] = selected or self._entry(exercise, None)
            if selected:
                reference = ExerciseReference(**self.identities[exercise["id"]])
                self.library.select(reference, selected["id"])
                self.selected[exercise["id"]] = selected
                checks = inspect_images(
                    selected["content"]["guidance"]["images"],
                    lambda image: self.assets.read(image["sha256"]),
                )
                eligible = assess_eligibility(
                    selected["content"],
                    selected["reference"]["sha256"],
                    checks,
                    None,
                    removed=bool(
                        reference.source == "bundled"
                        and self.catalog.get(reference.key)["withdrawn"]
                    ),
                ).eligible
                self.library.set_enabled(reference, bool(exercise["active"]) and eligible)

    def _attachment(self, review):
        path = review.get("review_answer_file")
        if not path:
            return None
        try:
            data = managed_path(self.root, path).read_bytes()
        except (OSError, ValueError):
            digest = None
        else:
            digest = hashlib.sha256(data).hexdigest()
        return {
            "path": path,
            "sha256": digest,
            "available": digest is not None,
            "original_name": review.get("review_answer_original_name"),
            "provenance": "migration_time",
            "original_review": review,
        }

    def _action(self, row, entry, doses, *, snapshot=False):
        sets = [
            {
                "order": dose["set_order"],
                "value": dose["planned_value" if snapshot else "value"],
                "unit": dose["planned_unit" if snapshot else "unit"],
                "per_side": bool(dose["planned_per_side" if snapshot else "per_side"]),
                "note": dose["plan_note_snapshot" if snapshot else "note"],
                "rest_after_set_seconds": None,
            }
            for dose in doses
        ]
        return {
            "kind": "action",
            "item_id": f"migration.action.{row['id']}",
            "order": row["plan_action_order" if snapshot else "action_order"],
            "phase": row["phase_snapshot" if snapshot else "phase"],
            "exercise": entry["content"]["exercise"],
            "exercise_name": row["exercise_name_snapshot"]
            if snapshot
            else entry["content"]["canonical_name"],
            "content": entry["reference"],
            "classification": entry["content"]["classification"],
            "sets": sets,
            "first_side": None,
            "rest_between_sides_seconds": None,
            "rest_after_action_seconds": row[
                "rest_seconds_snapshot" if snapshot else "rest_seconds"
            ],
            "note": row["plan_note_snapshot" if snapshot else "note"],
            "dose_scope": "per_side_aggregate" if any(s["per_side"] for s in sets) else "whole",
            "provenance": {
                "kind": "migration_time",
                "source_id": row["id"],
                "side_order_recorded": False,
                "set_rest_recorded": False,
            },
        }

    def _plans(self):
        for plan in self.old["training_plan"]:
            self.db.execute(
                "INSERT INTO group_plan VALUES (?,?,?,?)",
                (plan["id"], plan["name"], plan["active_revision_id"], plan["created_at"]),
            )
        for revision in self.old["training_plan_revision"]:
            plan = next(p for p in self.old["training_plan"] if p["id"] == revision["plan_id"])
            imported = next(iter(self._related("plan_import", "revision_id", revision["id"])), None)
            self.db.execute(
                "INSERT INTO group_plan_revision(id,plan_id,revision_number,status,name,purpose,"
                "rationale,source_json,created_at,migration_json) "
                "VALUES (?,?,?,'draft',?,?,?,?,?,?)",
                (
                    revision["id"],
                    plan["id"],
                    revision["revision_number"],
                    plan["name"],
                    revision["purpose"],
                    imported["rationale"] if imported else "",
                    "null",
                    revision["created_at"],
                    encode(
                        {
                            "kind": "migration_time",
                            "at": self.now,
                            "activation_time_recorded": False,
                            "original_revision": revision,
                        }
                    ),
                ),
            )
            for day in self._related("training_plan_day", "revision_id", revision["id"]):
                self.db.execute(
                    "INSERT INTO group_plan_day VALUES (?,?,?,?)",
                    (day["id"], revision["id"], day["day_order"], day["name"]),
                )
                for action in self._related("training_plan_action", "day_id", day["id"]):
                    entry = self.fallback[action["exercise_id"]]
                    doses = self._related("training_plan_set", "action_id", action["id"])
                    value = self._action(action, entry, doses)
                    item = self.plans._insert_item(revision["id"], day["id"], value, None)
                    self.provenance.map("training_plan_action", action["id"], "item", item)
                    for old_set, new_set in zip(
                        doses,
                        self.db.execute(
                            "SELECT id FROM group_plan_set WHERE item_id=? ORDER BY set_order",
                            (item,),
                        ),
                    ):
                        self.provenance.map("training_plan_set", old_set["id"], "set", new_set[0])
                    if revision["status"] != "draft":
                        self.plans.pin(
                            revision["id"],
                            value["item_id"],
                            entry["id"],
                            {
                                "reviewed": None,
                                "eligible": None,
                                "image_checks": [],
                                "events": [],
                                "observed_at": self.now,
                                "provenance": "migration_time",
                            },
                            self.now,
                        )
            self.db.execute(
                "UPDATE group_plan_revision SET status=? WHERE id=?",
                (revision["status"], revision["id"]),
            )
            self.provenance.map(
                "training_plan_revision", revision["id"], "revision", revision["id"]
            )

    def _sessions(self):
        for session in sorted(
            self.old["training_session"], key=lambda row: row["status"] in ("open", "paused")
        ):
            source_actions = sorted(
                self._related("training_session_action", "session_id", session["id"]),
                key=lambda row: (row["plan_day_order"], row["plan_action_order"]),
            )
            occurrences = [
                self._occurrence(action, index) for index, action in enumerate(source_actions)
            ]
            revision = self.plans.get(session["plan_revision_id"])
            # The session's prescription and pins describe its recorded revisions, never the
            # migration-time bindings of its plan. Unknown historical metadata stays provenance.
            frozen = deepcopy(revision)
            days = {}
            frozen["pins"] = []
            for row in occurrences:
                day = days.setdefault(
                    row["day_order"],
                    {
                        "order": row["day_order"],
                        "name": session["plan_day_name_snapshot"],
                        "items": [],
                    },
                )
                day["items"].append(row["action"])
                frozen["pins"].append(
                    {
                        "item_key": row["item_id"],
                        "content_id": row["content_id"],
                        "review": row["activation_review"],
                        "pinned_at": self.now,
                    }
                )
            frozen["payload"]["plan"]["days"] = list(days.values())
            snapshot = {
                "revision": frozen,
                "day": next(iter(days.values()), None),
                "training_date": session["training_date"],
                "unreviewed": [],
                "catalog_version": None,
                "provenance": {
                    "kind": "stored_session",
                    "original_session": session,
                    "position_recorded": False,
                },
            }
            position = next(
                (
                    row["position"]
                    for row, old in zip(occurrences, source_actions)
                    if old["result"] is None
                ),
                0,
            )
            self.db.execute(
                "INSERT INTO group_session(id,revision_id,training_date,status,position,"
                "snapshot_json,started_at) VALUES (?,?,?,'open',?,?,?)",
                (
                    session["id"],
                    session["plan_revision_id"],
                    session["training_date"],
                    position,
                    encode(snapshot),
                    session["started_at"],
                ),
            )
            for occurrence, action in zip(occurrences, source_actions):
                self.db.execute(
                    "INSERT INTO group_session_occurrence VALUES (?,?,?,?,?)",
                    (
                        action["id"],
                        session["id"],
                        occurrence["position"],
                        occurrence["content_id"],
                        encode(occurrence),
                    ),
                )
                self.provenance.map(
                    "training_session_action", action["id"], "occurrence", action["id"]
                )
                if action["result"] is not None:
                    self.sessions.record(
                        action["id"], action["result"], action["note"], self._actual(action), None
                    )
            self._session_evidence(session)
            self.db.execute(
                "UPDATE group_session SET status=?,ended_at=?,abort_reason=?,abort_note=? "
                "WHERE id=?",
                (
                    session["status"],
                    session["finished_at"],
                    session["abort_reason"],
                    session["abort_note"],
                    session["id"],
                ),
            )
            self.provenance.map("training_session", session["id"], "session", session["id"])

    def _occurrence(self, action, position):
        action = deepcopy(action)
        if self.original["schema"] < 10:
            for field in ("phase_snapshot", "rest_seconds_snapshot", "plan_note_snapshot"):
                action[field] = None
        revision = self.revision_rows.get(action["guidance_revision_id"])
        exercise_id = action["exercise_id"] or (revision["exercise_id"] if revision else None)
        if exercise_id not in self.exercise_rows:
            exercise_id = -action["id"]
            self.identities[exercise_id] = {
                "source": "custom",
                "key": self._key(f"unknown.{action['id']}"),
            }
            exercise = {
                "id": exercise_id,
                "canonical_name": action["exercise_name_snapshot"],
                "category": "",
                "equipment_summary": "",
            }
        else:
            exercise = self.exercise_rows[exercise_id]
        areas = json.loads(action["body_areas_snapshot_json"])
        entry = self._entry(
            exercise,
            revision,
            historical_name=action["exercise_name_snapshot"],
            historical_areas=[[area["name"], area["is_primary"]] for area in areas],
        )
        doses = self._related("training_session_set", "session_action_id", action["id"])
        if self.original["schema"] < 10:
            doses = [{**dose, "plan_note_snapshot": None} for dose in doses]
        value = self._action(action, entry, doses, snapshot=True)
        reviewed = action["guidance_reviewed_snapshot"]
        reviewed = None if reviewed is None else bool(reviewed)
        return {
            "position": position,
            "day_order": action["plan_day_order"],
            "day_name": "",
            "item_id": value["item_id"],
            "item_order": value["order"],
            "member_order": None,
            "group_id": None,
            "group": None,
            "round_number": None,
            "side": None,
            "phase": action["phase_snapshot"],
            "action": value,
            "dose_scope": value["dose_scope"],
            "rest_after_seconds": action["rest_seconds_snapshot"],
            "rest_boundary": "action_exit",
            "content_id": entry["id"],
            "content": entry["content"],
            "content_reference": entry["reference"],
            "body_areas": areas,
            "activation_review": {"reviewed": None, "provenance": "not_recorded"},
            "start_review": {
                "eligibility": {"reviewed": reviewed, "images_ready": None},
                "events": [],
                "observed_at": None,
                "provenance": "stored_snapshot",
            },
            "migration": {
                "original_action": action,
                "original_sets": doses,
                "guidance_recorded": revision is not None,
            },
        }

    def _actual(self, action):
        actual = self._related("training_session_actual_set", "session_action_id", action["id"])
        if not actual:
            actual = [
                {
                    "actual_order": dose["set_order"],
                    "value": dose["actual_value"],
                    "unit": dose["actual_unit"],
                    "per_side": dose["actual_per_side"],
                }
                for dose in self._related("training_session_set", "session_action_id", action["id"])
                if dose["actual_value"] is not None
            ]
        return [
            {
                "order": row["actual_order"],
                "value": row["value"],
                "unit": row["unit"],
                "side": None,
                "per_side": row["per_side"],
                "note": "",
                "provenance": "stored_actual",
            }
            for row in actual
        ]

    def _session_evidence(self, session):
        identifier = session["id"]
        for event in self._related("session_event", "session_id", identifier):
            self.sessions.event(
                identifier, "imported_event", {"original": event}, event["occurred_at"]
            )
        for audit in self._related("session_result_retraction", "session_id", identifier):
            self.sessions.event(
                identifier, "imported_retraction", {"original": audit}, audit["retracted_at"]
            )
        for audit in self._related("note_correction_audit", "session_id", identifier):
            self.sessions.event(
                identifier, "imported_note_correction", {"original": audit}, audit["corrected_at"]
            )
        feedback = next(iter(self._related("next_day_feedback", "session_id", identifier)), None)
        if feedback:
            values = {
                row["body_area_name_snapshot"]: row["value"]
                for row in self._related("next_day_feedback_area", "feedback_id", feedback["id"])
            }
            self.sessions.save_feedback(
                identifier, values, feedback["overall_note"], feedback["submitted_at"]
            )
            self.provenance.map("next_day_feedback", feedback["id"], "feedback_session", identifier)

    def _registrations(self):
        for kind, table in (("import", "plan_import"), ("export", "ai_export")):
            for row in self.old[table]:
                revision_id = row.get("revision_id")
                session_id = row.get("session_id", row.get("source_session_id"))
                facts = {
                    "original": row,
                    "path": row.get("file_path", row.get("source_path")),
                    "sha256": None,
                    "available": False,
                }
                # 旧运行时按平台原生分隔符记录路径（Windows 上是反斜杠）；
                # 查找原件时规范化为可移植分隔符，登记中的原值保持逐字。
                path = facts["path"]
                lookup = path.replace("\\", "/") if isinstance(path, str) else path
                try:
                    data = managed_path(self.root, lookup).read_bytes()
                except (OSError, ValueError, TypeError):
                    pass
                else:
                    facts.update(sha256=hashlib.sha256(data).hexdigest(), available=True)
                self.db.execute(
                    "INSERT INTO conversion_registration VALUES (?,?,?,?,?)",
                    (kind, row["id"], revision_id, session_id, encode(facts)),
                )
                self.provenance.map(
                    table, row["id"], "registration", {"kind": kind, "id": row["id"]}
                )
        # Keep the new export namespace above every externally referenced original ID.
        maximum = max((row["id"] for row in self.old["ai_export"]), default=0)
        self.provenance.map("ai_export", "namespace", "reserved_through", maximum)


def validate_catalog_conversion(root, catalog):
    """Read-only gate before publication and after publication; no repository writes."""
    inspect_existing(root)
    config = json.loads((Path(root) / CONFIG_FILENAME).read_text(encoding="utf-8"))
    if config.get("library_model") != LIBRARY_MODEL:
        raise UpgradeRecoveryError("Converted model configuration is missing.")
    with closing(_read_connection(root)) as db:
        run = db.execute("SELECT * FROM conversion_run WHERE id=1").fetchone()
        if run is None:
            raise UpgradeRecoveryError("Conversion facts are missing.")
        original = {"schema": run["source_schema"], "tables": {}, "config": None}
        manifest = json.loads(run["manifest_json"])
        for path, expected in manifest["resources"].items():
            data = managed_path(root, path).read_bytes()
            if (
                len(data) != expected["bytes"]
                or hashlib.sha256(data).hexdigest() != expected["sha256"]
            ):
                raise UpgradeRecoveryError(
                    "Original managed resource bytes changed during conversion."
                )
        original["tables"] = {table: [] for table in manifest["counts"]}
        for row in db.execute("SELECT * FROM conversion_original ORDER BY rowid"):
            if row["source_table"] == "app_config":
                original["config"] = json.loads(row["row_json"])
            else:
                original["tables"][row["source_table"]].append(json.loads(row["row_json"]))
        if content_sha256(original) != run["source_sha256"]:
            raise UpgradeRecoveryError("Original conversion facts failed preservation validation.")
        tables = {row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        if tables.intersection(OLD_TABLES):
            raise UpgradeRecoveryError("Obsolete live tables remain after conversion.")
        for old, new in (
            ("training_plan", "group_plan"),
            ("training_plan_revision", "group_plan_revision"),
            ("training_session", "group_session"),
            ("training_session_action", "group_session_occurrence"),
        ):
            expected = {row["id"] for row in original["tables"].get(old, [])}
            actual = {row[0] for row in db.execute(f"SELECT id FROM {new}")}
            if expected != actual:
                raise UpgradeRecoveryError(
                    "Converted external identities do not match original facts."
                )
        library, assets = LibraryRepository(db), SnapshotAssets(root)
        for row in db.execute("SELECT id FROM library_content"):
            entry = library.content(row[0])
            for digest in entry["assets"].values():
                assets.read(digest)
        for row in GroupSessionRepository(db).history():
            if len(row["occurrences"]) == 0 and row["status"] in ("open", "paused"):
                raise UpgradeRecoveryError("An unfinished session has no recorded prescription.")
        _validate_mapped_facts(db, original, root, catalog)


def _validate_mapped_facts(db, original, root, catalog):
    """Compare interpreted destinations against source rows, not merely archived copies."""

    def require(actual, expected):
        if actual != expected:
            raise UpgradeRecoveryError("Converted facts do not match their original records.")

    tables = original["tables"]

    def source(table):
        return tables.get(table, [])

    library = LibraryRepository(db)
    for old in source("exercise_guidance_revision"):
        mapped = db.execute(
            "SELECT target_json FROM conversion_mapping WHERE source_table=? "
            "AND source_key=? AND target_kind='content'",
            ("exercise_guidance_revision", str(old["id"])),
        ).fetchone()
        if mapped is None:
            raise UpgradeRecoveryError("A guidance revision was not converted.")
        entry = library.content(json.loads(mapped[0]))
        require(entry["provenance"]["original_revision"], old)
        expected_guidance = json.loads(old["guidance_json"])
        require(entry["provenance"]["original_guidance"], expected_guidance)
        for key, value in expected_guidance.items():
            if key not in ("images", "review"):
                require(entry["content"]["guidance"][key], value)
    for old in source("exercise"):
        state = db.execute(
            "SELECT * FROM library_state WHERE reference_id=?", (old["id"],)
        ).fetchone()
        require(state is not None, True)
        selected = old.get("active_guidance_revision_id")
        if selected is None:
            require(state["selected_content_id"], None)
            require(state["enabled"], 0)
        else:
            entry = library.content(state["selected_content_id"])
            require(entry["provenance"]["original_revision"]["id"], selected)
            checks = inspect_images(
                entry["content"]["guidance"]["images"],
                lambda image: SnapshotAssets(root).read(image["sha256"]),
            )
            reference = entry["content"]["exercise"]
            bundled = catalog.get(reference["key"]) if reference["source"] == "bundled" else None
            eligible = assess_eligibility(
                entry["content"],
                entry["reference"]["sha256"],
                checks,
                None,
                removed=bool(bundled and bundled["withdrawn"]),
            )
            require(bool(state["enabled"]), bool(old["active"]) and eligible.eligible)
    plans = GroupPlanRepository(db)
    for old in source("training_plan"):
        row = db.execute("SELECT * FROM group_plan WHERE id=?", (old["id"],)).fetchone()
        require(
            (row["name"], row["active_revision_id"], row["created_at"]),
            (old["name"], old["active_revision_id"], old["created_at"]),
        )
    for old in source("training_plan_revision"):
        revision = plans.get(old["id"])
        for field in ("plan_id", "revision_number", "status", "purpose", "created_at"):
            require(revision[field], old[field])
        require(revision["activated_at"], None)
        for day in revision["payload"]["plan"]["days"]:
            original_day = next(
                row
                for row in source("training_plan_day")
                if row["revision_id"] == old["id"] and row["day_order"] == day["order"]
            )
            require(day["name"], original_day["name"])
            actions = [
                row for row in source("training_plan_action") if row["day_id"] == original_day["id"]
            ]
            require(len(day["items"]), len(actions))
            for item, action in zip(
                day["items"], sorted(actions, key=lambda row: row["action_order"])
            ):
                require(
                    (item["order"], item["phase"], item["note"], item["rest_after_action_seconds"]),
                    (
                        action["action_order"],
                        action["phase"],
                        action["note"],
                        action["rest_seconds"],
                    ),
                )
                doses = sorted(
                    (
                        row
                        for row in source("training_plan_set")
                        if row["action_id"] == action["id"]
                    ),
                    key=lambda row: row["set_order"],
                )
                require(
                    [
                        (d["order"], d["value"], d["unit"], d["per_side"], d["note"])
                        for d in item["sets"]
                    ],
                    [
                        (
                            d["set_order"],
                            d["value"],
                            d["unit"],
                            bool(d["per_side"]),
                            d.get("note", ""),
                        )
                        for d in doses
                    ],
                )
    sessions = GroupSessionRepository(db)
    for old in source("training_session"):
        session = sessions.get(old["id"])
        require(
            (
                session["revision_id"],
                session["training_date"],
                session["status"],
                session["started_at"],
                session["ended_at"],
                session["abort_reason"],
                session["abort_note"],
            ),
            (
                old["plan_revision_id"],
                old["training_date"],
                old["status"],
                old["started_at"],
                old["finished_at"],
                old["abort_reason"],
                old["abort_note"],
            ),
        )
        for occurrence in session["occurrences"]:
            action = next(
                row for row in source("training_session_action") if row["id"] == occurrence["id"]
            )
            require(
                (occurrence["result"], occurrence["note"], occurrence["action"]["exercise_name"]),
                (action["result"], action["note"], action["exercise_name_snapshot"]),
            )
            require(occurrence["recorded_at"], None)
            require(
                occurrence["start_review"]["eligibility"]["reviewed"],
                action.get("guidance_reviewed_snapshot"),
            )
            require(occurrence["start_review"]["eligibility"]["images_ready"], None)
            require(occurrence["phase"], action.get("phase_snapshot"))
            require(occurrence["rest_after_seconds"], action.get("rest_seconds_snapshot"))
            require(occurrence["action"]["note"], action.get("plan_note_snapshot"))
            original_areas = json.loads(action["body_areas_snapshot_json"])
            expected_areas = [{"name": value, "is_primary": None} if isinstance(value, str)
                              else value for value in original_areas]
            require(occurrence["body_areas"], expected_areas)
            planned = sorted((row for row in source("training_session_set")
                              if row["session_action_id"] == action["id"]),
                             key=lambda row: row["set_order"])
            require([(dose["order"], dose["value"], dose["unit"], dose["per_side"], dose["note"])
                     for dose in occurrence["action"]["sets"]],
                    [(dose["set_order"], dose["planned_value"], dose["planned_unit"],
                      bool(dose["planned_per_side"]), dose.get("plan_note_snapshot"))
                     for dose in planned])
            actual = [
                row
                for row in source("training_session_actual_set")
                if row["session_action_id"] == action["id"]
            ]
            if not actual:
                actual = [
                    {
                        "actual_order": d["set_order"],
                        "value": d["actual_value"],
                        "unit": d["actual_unit"],
                        "per_side": d["actual_per_side"],
                    }
                    for d in source("training_session_set")
                    if d["session_action_id"] == action["id"] and d["actual_value"] is not None
                ]
            require(
                [
                    (d["order"], d["value"], d["unit"], d.get("per_side"))
                    for d in occurrence["actual_sets"]
                ],
                [
                    (d["actual_order"], d["value"], d["unit"], d["per_side"])
                    for d in sorted(actual, key=lambda row: row["actual_order"])
                ],
            )
        old_feedback = next(
            (row for row in source("next_day_feedback") if row["session_id"] == old["id"]), None
        )
        if old_feedback:
            feedback = session["feedback"]
            require(
                (feedback["overall_note"], feedback["submitted_at"]),
                (old_feedback["overall_note"], old_feedback["submitted_at"]),
            )
            require(
                {row["name"]: row["value"] for row in feedback["areas"]},
                {
                    row["body_area_name_snapshot"]: row["value"]
                    for row in source("next_day_feedback_area")
                    if row["feedback_id"] == old_feedback["id"]
                },
            )
        else:
            require(session["feedback"], None)
        for table, kind in (("session_event", "imported_event"),
                            ("session_result_retraction", "imported_retraction"),
                            ("note_correction_audit", "imported_note_correction")):
            require([event["facts"]["original"] for event in session["events"]
                     if event["kind"] == kind],
                    [row for row in source(table) if row["session_id"] == old["id"]])
