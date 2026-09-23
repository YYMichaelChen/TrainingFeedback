"""V2 draft editing and activation: exact content targets, stale checks and immutable pins."""

from copy import deepcopy
from dataclasses import asdict

from ..data.plan_contract import plan_v2_schema
from ..domain.catalog import ExerciseReference, content_sha256
from ..domain.group_plans import (
    diff_plans,
    identity_rows,
    plan_actions,
    validate_plan_payload,
    validate_stored_plan,
)
from .library_workflow import LibraryTarget


class GroupPlanService:
    def __init__(self, repository, library):
        self.repository, self.library = repository, library
        self.schema = plan_v2_schema()

    def list_plans(self):
        return self.repository.list_plans()

    def active_revisions(self):
        return [self.get(plan["active_revision_id"]) for plan in self.list_plans()
                if plan["active_revision_id"] is not None]

    def revisions(self, plan_id):
        return self.repository.revisions(plan_id)

    def get(self, revision_id):
        return self.repository.get(revision_id)

    def content_issues(self, revision_id):
        issues = []
        for _day, _item, action in plan_actions(self.get(revision_id)["payload"]["plan"]):
            target = LibraryTarget(ExerciseReference(**action["exercise"]), action["content"])
            status = self.library.eligibility(target)
            reasons = list(status.reasons)
            if not self.library.user.state(target.exercise)["enabled"]:
                reasons.append("disabled")
            if reasons:
                issues.append({"item_id": action["item_id"], "name": action["exercise_name"],
                               "reasons": reasons})
        return issues

    def validate(self, payload, *, activation=False, stored=None):
        validated = (validate_plan_payload(payload, self.schema, activation=activation)
                     if stored is None else validate_stored_plan(payload, self.schema, {
                         action["item_id"]: action for _, _, action in
                         plan_actions(stored["payload"]["plan"])
                     }, activation=activation))
        for _day, _item, action in plan_actions(validated["plan"]):
            reference = ExerciseReference(**action["exercise"])
            entry = self.library.resolve(reference, action["exercise_name"], action["content"])
            if entry["content"]["classification"] != action["classification"]:
                raise ValueError("Plan classification does not match the exact content revision.")
        return validated

    def _lineage(self, plan_id, payload):
        if plan_id is None:
            return
        new = identity_rows(payload["plan"])
        for revision in self.repository.revisions(plan_id):
            for key, (_path, old) in identity_rows(revision["payload"]["plan"]).items():
                if key not in new:
                    continue
                current = new[key][1]
                if old.get("exercise") != current.get("exercise"):
                    raise ValueError("A reused item identity cannot refer to another exercise.")

    def create(self, payload, *, plan_id=None):
        with self.library._action():
            payload = self.validate(payload)
            self.repository.check_source(payload.get("source", {}))
            self._lineage(plan_id, payload)
            return self.repository.create(payload, self.library.clock.now().isoformat(), plan_id)

    def save(self, revision_id, payload, *, expected_token):
        with self.library._action():
            current = self.get(revision_id)
            payload = self.validate(payload, stored=current)
            self.repository.check_source(payload.get("source", {}))
            self._lineage(current["plan_id"], payload)
            self.repository.replace(revision_id, payload, expected_token)

    def clone(self, revision_id):
        with self.library._action():
            source = self.get(revision_id)
            return self.repository.create(
                source["payload"], self.library.clock.now().isoformat(), source["plan_id"]
            )

    def _targets(self, payload):
        return [
            LibraryTarget(ExerciseReference(**action["exercise"]), action["content"])
            for _day, _item, action in plan_actions(payload["plan"])
        ]

    def preview(self, revision_id):
        revision = self.get(revision_id)
        if revision["status"] != "draft":
            raise ValueError("Only draft revisions can be activated.")
        payload = self.validate(revision["payload"], activation=True, stored=revision)
        targets = self._targets(payload)
        unreviewed = self.library.require_for_activation(targets)
        active = self.repository.active(revision["plan_id"])
        review_state = [self.library.review_events(target) for target in targets]
        eligibility = [asdict(self.library.eligibility(target)) for target in targets]
        token = content_sha256(
            {
                "revision": revision,
                "active_id": active["id"] if active else None,
                "unreviewed": unreviewed,
                "reviews": review_state,
                "eligibility": eligibility,
            }
        )
        return {
            "revision": revision,
            "unreviewed": unreviewed,
            "token": token,
            "changes": diff_plans(active["payload"]["plan"] if active else None, payload["plan"]),
        }

    def activate(self, revision_id, *, expected_preview: str, user_confirmed: bool):
        if user_confirmed is not True:
            raise ValueError("Explicit confirmation is required.")
        with self.library._action():
            preview = self.preview(revision_id)
            if preview["token"] != expected_preview:
                raise ValueError("The activation preview changed. Review it again.")
            now = self.library.clock.now().isoformat()
            for _day, _item, action in plan_actions(preview["revision"]["payload"]["plan"]):
                target = LibraryTarget(ExerciseReference(**action["exercise"]), action["content"])
                identifier = self.library._retain_target(target)
                status = self.library.eligibility(target)
                if not status.eligible:
                    raise ValueError("Content became ineligible during plan activation.")
                self.repository.pin(
                    revision_id,
                    action["item_id"],
                    identifier,
                    {
                        "reviewed": status.reviewed,
                        "eligible": status.eligible,
                        "image_checks": [asdict(check) for check in status.image_checks],
                        "events": self.library.review_events(target),
                        "observed_at": now,
                        "provenance": "plan_activation",
                    },
                    now,
                )
            self.repository.activate(revision_id, now)

    def exercise_choices(self):
        choices = []
        for row in self.library.browse():
            if row["eligibility"].removed:
                continue
            entry = row["selected"] or row["display"]
            content = entry["content"]
            choices.append(
                {
                    "exercise": deepcopy(content["exercise"]),
                    "exercise_name": content["canonical_name"],
                    "content": deepcopy(entry["reference"]),
                    "classification": deepcopy(content["classification"]),
                }
            )
        return choices
