"""Root-local lifecycle journal, tombstones and inspectable reference impact."""

import hashlib
import json

from ..domain.library_lifecycle import contains_exercise
from .catalog_resources import managed_path


def encode(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, allow_nan=False)


class LibraryLifecycleRepository:
    def __init__(self, connection, root):
        self.connection, self.root = connection, root

    def get(self, identifier):
        row = self.connection.execute(
            "SELECT * FROM library_lifecycle_request WHERE id=?", (identifier,),
        ).fetchone()
        if row is None:
            raise ValueError("Lifecycle request was not found.")
        request = dict(row)
        request["preview"] = json.loads(request.pop("preview_json"))
        request["events"] = []
        for event in self.connection.execute(
            "SELECT * FROM library_lifecycle_event WHERE request_id=? ORDER BY id", (identifier,),
        ):
            event = dict(event)
            event["preview"] = json.loads(event.pop("preview_json"))
            request["events"].append(event)
        request["status"] = request["events"][-1]["kind"]
        return request

    def requests(self):
        return [self.get(row[0]) for row in self.connection.execute(
            "SELECT id FROM library_lifecycle_request ORDER BY id DESC"
        )]

    def create(self, operation, reason, preview, now):
        return self.connection.execute(
            "INSERT INTO library_lifecycle_request(operation,reason,requested_at,preview_json) "
            "VALUES (?,?,?,?)", (operation, reason, now, encode(preview)),
        ).lastrowid

    def append(self, identifier, kind, source, occurred_at, note, preview, now):
        return self.connection.execute(
            "INSERT INTO library_lifecycle_event(request_id,kind,source,occurred_at,"
            "confirmed_at,note,preview_json) VALUES (?,?,?,?,?,?,?)",
            (identifier, kind, source, occurred_at, now, note, encode(preview)),
        ).lastrowid

    def tombstone(self, reference_id, disposition, event_id):
        self.connection.execute(
            "INSERT INTO library_tombstone VALUES (?,?,?) ON CONFLICT(reference_id) "
            "DO UPDATE SET disposition=excluded.disposition,event_id=excluded.event_id",
            (reference_id, disposition, event_id),
        )

    def publisher_events(self, reference=None):
        rows = self.connection.execute(
            "SELECT p.*,r.source,r.stable_key FROM library_publisher_event p "
            "JOIN library_reference r ON r.id=p.reference_id ORDER BY p.id"
        )
        result = []
        for row in rows:
            if reference and (row["source"], row["stable_key"]) != (
                reference.source, reference.key,
            ):
                continue
            event = dict(row)
            event["content_reference"] = json.loads(event.pop("content_reference_json"))
            result.append(event)
        return result

    def observe_publisher(self, reference_id, version, manifest_hash, disposition, content, now):
        return self.connection.execute(
            "INSERT INTO library_publisher_event(reference_id,catalog_version,manifest_sha256,"
            "disposition,content_reference_json,observed_at) VALUES (?,?,?,?,?,?)",
            (reference_id, version, manifest_hash, disposition, encode(content), now),
        ).lastrowid

    def invalidate_plans(self, reference_id, event_id, *, publisher=False):
        self.connection.execute(
            "INSERT INTO library_plan_invalidation "
            "SELECT DISTINCT i.revision_id,?, ?, ? FROM group_plan_pin p "
            "JOIN group_plan_item i ON i.id=p.item_id "
            "JOIN library_content c ON c.id=p.content_id WHERE c.reference_id=? "
            "ON CONFLICT DO NOTHING",
            (reference_id, None if publisher else event_id, event_id if publisher else None,
             reference_id),
        )

    def impacts(self, exercise):
        plans, groups, sessions, reviews, exports = [], [], [], [], []
        for revision in self.connection.execute("SELECT * FROM group_plan_revision ORDER BY id"):
            matches = []
            for item in self.connection.execute(
                "SELECT i.*,d.day_order,p.item_key AS group_key,"
                "p.fields_json AS group_json FROM group_plan_item i "
                "JOIN group_plan_day d ON d.id=i.day_id "
                "LEFT JOIN group_plan_item p ON p.id=i.parent_id "
                "WHERE i.revision_id=? ORDER BY i.id", (revision["id"],),
            ):
                fields = json.loads(item["fields_json"])
                if fields.get("exercise") != exercise:
                    continue
                matches.append({"item_id": item["item_key"], "day_order": item["day_order"],
                                "content": fields["content"]})
                if item["parent_id"]:
                    groups.append({"revision_id": revision["id"], "group_id": item["group_key"],
                                   "name": json.loads(item["group_json"])["name"],
                                   "member_id": item["item_key"], "day_order": item["day_order"]})
            if matches:
                plans.append({key: revision[key] for key in
                              ("id", "plan_id", "name", "revision_number", "status", "edit_token")}
                             | {"items": matches})
        for session in self.connection.execute(
            "SELECT s.*, (SELECT MAX(id) FROM group_session_event WHERE session_id=s.id) "
            "AS event_id, (SELECT submitted_at FROM group_session_feedback WHERE session_id=s.id) "
            "AS feedback_at FROM group_session s ORDER BY s.id"
        ):
            if contains_exercise(json.loads(session["snapshot_json"]), exercise):
                sessions.append({key: session[key] for key in
                                 ("id", "revision_id", "training_date", "status", "version",
                                  "position", "event_id", "feedback_at")})
        for row in self.connection.execute(
            "SELECT e.id,e.content_id,e.event_type,e.content_sha256,e.confirmed_at "
            "FROM library_review_event e JOIN library_content c ON c.id=e.content_id "
            "JOIN library_reference r ON r.id=c.reference_id "
            "WHERE r.source=? AND r.stable_key=? ORDER BY e.id",
            (exercise["source"], exercise["key"]),
        ):
            reviews.append(dict(row))
        session_ids = {row["id"] for row in sessions}
        for row in self.connection.execute("SELECT * FROM group_plan_export ORDER BY id"):
            exported = dict(row)
            try:
                path = managed_path(self.root, row["directory"] + "/evidence.json")
                raw = path.read_bytes()
                evidence = json.loads(raw)
                exported["sha256"] = hashlib.sha256(raw).hexdigest()
                relevant = contains_exercise(evidence, exercise) or any(
                    session.get("id") in session_ids
                    for session in evidence.get("earlier_sessions", [])
                )
                exported["availability"] = "available"
            except (OSError, ValueError, TypeError, AttributeError):
                relevant = True  # Missing evidence cannot justify claiming no impact.
                exported.update(sha256=None, availability="unknown")
            if relevant:
                exports.append(exported)
        for row in self.connection.execute(
            "SELECT * FROM conversion_registration WHERE kind='export' ORDER BY id"
        ):
            facts = json.loads(row["facts_json"])
            # V1 evidence did not carry namespaced keys; retain conservative reference
            # impact rather than infer identity from a matching display name.
            exported = {"id": row["id"], "directory": facts["path"],
                        "provenance": "converted_registration", "reference_scope": "unknown"}
            try:
                raw = managed_path(self.root, facts["path"]).read_bytes()
                exported.update(sha256=hashlib.sha256(raw).hexdigest(), availability="available")
            except (OSError, ValueError, TypeError):
                exported.update(sha256=None, availability="unknown")
            exports.append(exported)
        return {"plans": plans, "groups": groups, "sessions": sessions,
                "reviews": reviews, "exports": exports}
