"""Transactional new-model execution, exact batch targets and frozen-history feedback."""

from dataclasses import asdict
from datetime import date

from ..data.database import transaction
from ..data.library_images import inspect_images
from ..domain.catalog import ExerciseReference, content_sha256
from ..domain.enums import AbortReason, ExerciseResult, FeedbackValue, SessionStatus
from ..domain.group_execution import (
    actual_doses,
    expand_day,
    final_status,
    round_members,
    session_feedback_areas,
)
from ..domain.group_plans import continuous_plan_day
from ..domain.training import has_previous_day_label, is_active_session, is_terminal_session
from .library_workflow import LibraryTarget


class GroupSessionService:
    def __init__(self, repository, plans, clock=None):
        self.repository = repository
        self.plans = plans
        self.library = plans.library
        self.clock = clock or self.library.clock

    def _transaction(self):
        return transaction(self.repository.connection, immediate=True)

    def get(self, identifier):
        return self.repository.get(identifier)

    def active(self):
        return self.repository.active()

    def history(self):
        return self.repository.history()

    def image(self, occurrence, index):
        entry = self.library.user.content(occurrence["content_id"])
        declaration = occurrence["content"]["guidance"]["images"][index]
        if declaration["status"] != "available":
            raise ValueError("Image is unavailable or invalid.")
        data = self.library._read_image(entry, declaration)
        if not inspect_images([declaration], lambda _: data)[0].valid:
            raise ValueError("Image is unavailable or invalid.")
        return data

    def previous_day(self, session):
        return has_previous_day_label(date.fromisoformat(session["training_date"]),
                                      SessionStatus(session["status"]), self.clock)

    def preview_start(self, revision_id, day_order=None):
        if day_order is not None and type(day_order) is not int:
            raise ValueError("Select a day from the displayed plan revision.")
        if self.active() is not None:
            raise ValueError("An unfinished session already exists. Resume it first.")
        revision = self.plans.get(revision_id)
        if revision["status"] != "active":
            raise ValueError("An active plan revision is required to start training.")
        if self.library.user.plan_invalidated(revision_id):
            raise ValueError("This plan was affected by removal; confirm a new plan revision.")
        day = (continuous_plan_day(revision["payload"]["plan"]) if day_order is None else
               next((day for day in revision["payload"]["plan"]["days"]
                     if day["order"] == day_order), None))
        if day is None:
            raise ValueError("Select a day from the displayed plan revision.")
        occurrences = expand_day(day)
        pins = {pin["item_key"]: pin for pin in revision["pins"]}
        actions = {row["item_id"]: row["action"] for row in occurrences}
        targets = {key: LibraryTarget(ExerciseReference(**action["exercise"]), action["content"])
                   for key, action in actions.items()}
        unreviewed = self.library.require_for_new_session(list(targets.values()))
        reviews = {}
        for key, target in targets.items():
            pin = pins[key]
            entry = self.library.user.content(pin["content_id"])
            if entry["reference"] != target.content:
                raise ValueError("The plan content pin does not match its prescription.")
            status = self.library.eligibility(target)
            reviews[key] = {"eligibility": asdict(status),
                            "events": self.library.review_events(target)}
            for row in occurrences:
                if row["item_id"] == key:
                    row.update(content_id=pin["content_id"], content=entry["content"],
                               content_reference=entry["reference"],
                               body_areas=[{"name": name, "is_primary": primary}
                                           for name, primary in entry["content"]["body_areas"]],
                               activation_review=pin["review"], start_review=reviews[key])
        value = {"revision": revision, "day": day, "occurrences": occurrences,
                 "unreviewed": list(unreviewed), "training_date": self.clock.today().isoformat(),
                 "catalog_version": self.library.catalog.version}
        return {**value, "token": content_sha256(value)}

    def start(self, revision_id, day_order=None, *, expected_preview, user_confirmed):
        self._confirmed(user_confirmed)
        with self._transaction():
            preview = self.preview_start(revision_id, day_order)
            if preview["token"] != expected_preview:
                raise ValueError("The start preview changed. Review it again.")
            now = self.clock.now().isoformat()
            if now[:10] != preview["training_date"]:
                raise ValueError("The start preview changed. Review it again.")
            for row in preview["occurrences"]:
                row["start_review"] = {**row["start_review"], "observed_at": now,
                                       "provenance": "session_start"}
            snapshot = {key: value for key, value in preview.items()
                        if key not in {"token", "occurrences"}}
            identifier = self.repository.create(
                revision_id, preview["training_date"], snapshot, preview["occurrences"], now,
            )
        return self.get(identifier)

    @staticmethod
    def _confirmed(value):
        if value is not True:
            raise ValueError("Explicit confirmation is required.")

    def _current(self, identifier, version, *, paused=False):
        session = self.get(identifier)
        if session["version"] != version:
            raise ValueError("The session changed. Reload the displayed session.")
        if session["status"] not in (("open", "paused") if paused else ("open",)):
            raise ValueError("Only an open session accepts this action.")
        return session

    @staticmethod
    def _occurrence(session, occurrence_id):
        row = next((row for row in session["occurrences"] if row["id"] == occurrence_id), None)
        if row is None:
            raise ValueError("Occurrence does not belong to this session.")
        return row

    def navigate(self, identifier, position, *, expected_version):
        with self._transaction():
            session = self._current(identifier, expected_version)
            if type(position) is not int or not 0 <= position < len(session["occurrences"]):
                raise ValueError("Invalid occurrence position.")
            if session["position"] != position:
                self.repository.touch(identifier, position=position)
        return self.get(identifier)

    def record(self, identifier, occurrence_id, result, *, actual=(), note="", expected_version):
        with self._transaction():
            session = self._current(identifier, expected_version)
            row = self._occurrence(session, occurrence_id)
            if row["position"] != session["position"]:
                raise ValueError("Record only the displayed occurrence.")
            if row["result"] is not None:
                raise ValueError("This occurrence already has a saved result.")
            doses = actual_doses(row, result, actual, note)
            self.repository.record(row["id"], ExerciseResult(result).value, note, doses,
                                   self.clock.now().isoformat())
            self.repository.touch(identifier)
        return self.get(identifier)

    def preview_round(self, identifier):
        session = self.get(identifier)
        if session["status"] != "open":
            raise ValueError("Only an open session accepts this action.")
        members = round_members(session)
        if not members:
            raise ValueError("This round has no unrecorded occurrences.")
        value = {"session_id": identifier, "version": session["version"],
                 "position": session["position"], "members": members}
        return {**value, "token": content_sha256(value)}

    def complete_round(self, identifier, *, expected_preview, user_confirmed):
        self._confirmed(user_confirmed)
        with self._transaction():
            preview = self.preview_round(identifier)
            if preview["token"] != expected_preview:
                raise ValueError("The round preview changed. Review it again.")
            now = self.clock.now().isoformat()
            batch_id = self.repository.batch(identifier, expected_preview,
                                             [row["id"] for row in preview["members"]], now)
            for row in preview["members"]:
                self.repository.record(row["id"], "completed", "",
                                       actual_doses(row, "completed", (), ""), now, batch_id)
            self.repository.touch(identifier)
        return self.get(identifier)

    def retract(self, identifier, *, occurrence_id=None, batch_id=None,
                expected_version, user_confirmed):
        self._confirmed(user_confirmed)
        if (occurrence_id is None) == (batch_id is None):
            raise ValueError("Select one occurrence or one complete batch to retract.")
        with self._transaction():
            session = self._current(identifier, expected_version)
            if batch_id is not None:
                batch = next((row for row in session["batches"] if row["id"] == batch_id), None)
                if batch is None:
                    raise ValueError("Batch does not belong to this session.")
                rows = [self._occurrence(session, key) for key in batch["members"]]
                if any(row["batch_id"] != batch_id or row["result"] is None for row in rows):
                    raise ValueError("This batch was already retracted or changed.")
            else:
                rows = [self._occurrence(session, occurrence_id)]
                if rows[0]["batch_id"] is not None:
                    raise ValueError("Retract this result using its complete batch.")
                if rows[0]["result"] is None:
                    raise ValueError("This occurrence has no saved result.")
            self.repository.event(identifier, "result_retracted",
                                  {"batch_id": batch_id, "before": rows},
                                  self.clock.now().isoformat())
            for row in rows:
                self.repository.clear_result(row["id"])
            self.repository.touch(identifier)
        return self.get(identifier)

    def pause(self, identifier, *, expected_version):
        with self._transaction():
            session = self._current(identifier, expected_version)
            now = self.clock.now().isoformat()
            self.repository.event(identifier, "paused", {"position": session["position"]}, now)
            self.repository.status(identifier, "paused", now)
        return self.get(identifier)

    def resume(self, identifier, *, expected_version):
        with self._transaction():
            session = self._current(identifier, expected_version, paused=True)
            if session["status"] == "paused":
                now = self.clock.now().isoformat()
                self.repository.event(identifier, "resumed", {"position": session["position"]}, now)
                self.repository.status(identifier, "open", now)
        return self.get(identifier)

    def finish(self, identifier, *, expected_version, user_confirmed):
        self._confirmed(user_confirmed)
        with self._transaction():
            session = self._current(identifier, expected_version)
            status = final_status(session)
            now = self.clock.now().isoformat()
            self.repository.event(identifier, "finished", {"status": status}, now)
            self.repository.status(identifier, status, now)
        return self.get(identifier)

    def proposed_status(self, identifier):
        return final_status(self.get(identifier))

    def abort(self, identifier, reason, note, *, expected_version, user_confirmed):
        self._confirmed(user_confirmed)
        if reason is None:
            raise ValueError("An abort reason is required.")
        reason = AbortReason(reason)
        if not isinstance(note, str):
            raise ValueError("Abort notes must be text.")
        with self._transaction():
            session = self._current(identifier, expected_version, paused=True)
            now = self.clock.now().isoformat()
            self.repository.event(identifier, "aborted", {
                "position": session["position"], "reason": reason, "note": note,
            }, now)
            self.repository.status(identifier, "aborted", now, reason, note)
        return self.get(identifier)

    def feedback_areas(self, session):
        return session_feedback_areas(session)

    def pending_feedback(self):
        return [session for session in self.history()
                if is_terminal_session(session["status"])
                and session["training_date"] < self.clock.today().isoformat()
                and session["feedback"] is None and self.feedback_areas(session)]

    def submit_feedback(self, identifier, values, note):
        with self._transaction():
            session = self.get(identifier)
            areas = self.feedback_areas(session)
            if (is_active_session(session["status"])
                    or session["training_date"] >= self.clock.today().isoformat()
                    or not areas):
                raise ValueError("This session is not eligible for next-day feedback.")
            if session["feedback"] is not None:
                raise ValueError("Next-day feedback has already been submitted.")
            if set(values) != set(areas) or not isinstance(note, str):
                raise ValueError("Feedback must contain exactly the derived training areas.")
            normalized = {area: None if values[area] is None else FeedbackValue(values[area]).value
                          for area in areas}
            self.repository.save_feedback(identifier, normalized, note,
                                          self.clock.now().isoformat())
        return self.get(identifier)["feedback"]

    def correct_note(self, identifier, target, new_value, *, expected_value):
        with self._transaction():
            session = self.get(identifier)
            if not is_terminal_session(session["status"]) or not isinstance(new_value, str):
                raise ValueError("Only terminal session notes can be corrected.")
            if target == "overall_note":
                if session["feedback"] is None:
                    raise ValueError("Feedback has not been submitted.")
                old_value = session["feedback"]["overall_note"]
                occurrence_id = None
            elif type(target) is int:
                row = self._occurrence(session, target)
                if row["result"] is None:
                    raise ValueError("Unanswered work has no result note to correct.")
                occurrence_id, old_value = target, row["note"]
            else:
                raise ValueError("Only result and feedback notes can be corrected.")
            if old_value != expected_value:
                raise ValueError("The note changed. Reload the displayed session.")
            self.repository.event(identifier, "note_correction", {
                "target": "overall_note" if occurrence_id is None else "occurrence_note",
                "occurrence_id": occurrence_id, "old_value": old_value, "new_value": new_value,
            }, self.clock.now().isoformat())
        return self.get(identifier)
