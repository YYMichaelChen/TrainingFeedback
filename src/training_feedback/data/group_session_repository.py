"""Occurrence, result and append-only evidence storage; services own transactions."""

import json


def encode(value):
    return json.dumps(value, ensure_ascii=False, allow_nan=False)


class GroupSessionRepository:
    def __init__(self, connection):
        self.connection = connection

    def active(self):
        row = self.connection.execute(
            "SELECT id FROM group_session WHERE status IN ('open','paused')"
        ).fetchone()
        return self.get(row[0]) if row else None

    def history(self):
        return [self.get(row[0]) for row in self.connection.execute(
            "SELECT id FROM group_session ORDER BY training_date DESC,id DESC"
        )]

    def get(self, identifier):
        row = self.connection.execute(
            "SELECT * FROM group_session WHERE id=?", (identifier,)
        ).fetchone()
        if row is None:
            raise ValueError("Session was not found.")
        session = dict(row)
        session["snapshot"] = json.loads(session.pop("snapshot_json"))
        session["occurrences"] = []
        for occurrence in self.connection.execute(
            "SELECT o.*, r.result,r.note,r.recorded_at,r.batch_id FROM group_session_occurrence o "
            "LEFT JOIN group_occurrence_result r ON r.occurrence_id=o.id "
            "WHERE o.session_id=? ORDER BY o.position", (identifier,)
        ):
            value = dict(occurrence)
            value.update(json.loads(value.pop("snapshot_json")))
            value["actual_sets"] = [dict(dose) for dose in self.connection.execute(
                'SELECT set_order AS "order",value,unit,side,note,provenance,per_side '
                "FROM group_actual_set WHERE occurrence_id=? ORDER BY set_order", (value["id"],)
            )]
            for dose in value["actual_sets"]:
                if dose["per_side"] is None and dose["provenance"] != "stored_actual":
                    dose.pop("per_side")
                elif dose["per_side"] is not None:
                    dose["per_side"] = bool(dose["per_side"])
            session["occurrences"].append(value)
        session["events"] = [
            {"id": event["id"], "kind": event["kind"], "occurred_at": event["occurred_at"],
             "facts": json.loads(event["facts_json"])}
            for event in self.connection.execute(
                "SELECT * FROM group_session_event WHERE session_id=? ORDER BY id", (identifier,)
            )
        ]
        session["batches"] = [
            {"id": batch["id"], "preview_token": batch["preview_token"],
             "members": json.loads(batch["members_json"]), "created_at": batch["created_at"]}
            for batch in self.connection.execute(
                "SELECT * FROM group_session_batch WHERE session_id=? ORDER BY id", (identifier,)
            )
        ]
        session["feedback"] = self.feedback(identifier)
        # Corrections are an append-only overlay. Original result/feedback notes remain intact.
        for event in session["events"]:
            if event["kind"] != "note_correction":
                continue
            facts = event["facts"]
            if facts["target"] == "overall_note":
                session["feedback"]["overall_note"] = facts["new_value"]
            else:
                occurrence = next(o for o in session["occurrences"]
                                  if o["id"] == facts["occurrence_id"])
                occurrence["note"] = facts["new_value"]
        return session

    def create(self, revision_id, training_date, snapshot, occurrences, now):
        identifier = self.connection.execute(
            "INSERT INTO group_session(revision_id,training_date,status,snapshot_json,started_at) "
            "VALUES (?,?,'open',?,?)", (revision_id, training_date, encode(snapshot), now)
        ).lastrowid
        for occurrence in occurrences:
            self.connection.execute(
                "INSERT INTO group_session_occurrence"
                "(session_id,position,content_id,snapshot_json) VALUES (?,?,?,?)",
                (identifier, occurrence["position"], occurrence["content_id"], encode(occurrence)),
            )
        self.event(identifier, "started", {"position": 0}, now)
        return identifier

    def touch(self, identifier, *, position=None):
        self.connection.execute(
            "UPDATE group_session SET version=version+1,position=COALESCE(?,position) WHERE id=?",
            (position, identifier),
        )

    def record(self, occurrence_id, result, note, actual, now, batch_id=None):
        self.connection.execute(
            "INSERT INTO group_occurrence_result VALUES (?,?,?,?,?)",
            (occurrence_id, result, note, now, batch_id),
        )
        for dose in actual:
            self.connection.execute(
                "INSERT INTO group_actual_set VALUES (?,?,?,?,?,?,?,?)",
                (occurrence_id, dose["order"], dose["value"], dose["unit"], dose["side"],
                 dose["note"], dose["provenance"], dose.get("per_side")),
            )

    def batch(self, identifier, token, members, now):
        return self.connection.execute(
            "INSERT INTO group_session_batch(session_id,preview_token,members_json,created_at) "
            "VALUES (?,?,?,?)", (identifier, token, encode(members), now),
        ).lastrowid

    def clear_result(self, occurrence_id):
        self.connection.execute("DELETE FROM group_actual_set WHERE occurrence_id=?",
                                (occurrence_id,))
        self.connection.execute("DELETE FROM group_occurrence_result WHERE occurrence_id=?",
                                (occurrence_id,))

    def event(self, identifier, kind, facts, now):
        self.connection.execute(
            "INSERT INTO group_session_event(session_id,kind,occurred_at,facts_json) "
            "VALUES (?,?,?,?)",
            (identifier, kind, now, encode(facts)),
        )

    def status(self, identifier, status, now, reason=None, note=None):
        terminal = status in ("completed", "partial", "aborted")
        self.connection.execute(
            "UPDATE group_session SET status=?,version=version+1,paused_at=?,ended_at=?,"
            "abort_reason=?,abort_note=? WHERE id=?",
            (status, now if status == "paused" else None, now if terminal else None,
             reason, note, identifier),
        )

    def feedback(self, identifier):
        row = self.connection.execute(
            "SELECT * FROM group_session_feedback WHERE session_id=?", (identifier,)
        ).fetchone()
        if row is None:
            return None
        return {**dict(row), "areas": [dict(area) for area in self.connection.execute(
            "SELECT name,value FROM group_session_feedback_area WHERE session_id=? ORDER BY rowid",
            (identifier,),
        )]}

    def save_feedback(self, identifier, values, note, now):
        self.connection.execute("INSERT INTO group_session_feedback VALUES (?,?,?)",
                                (identifier, note, now))
        for name, value in values.items():
            self.connection.execute("INSERT INTO group_session_feedback_area VALUES (?,?,?)",
                                    (identifier, name, value))

    def register_export(self, identifier, export_id):
        self.connection.execute("INSERT INTO group_session_export VALUES (?,?)",
                                (export_id, identifier))
