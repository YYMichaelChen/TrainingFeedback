"""V2 draft editing and activation: exact content targets, stale checks and immutable pins."""

from copy import deepcopy
from dataclasses import asdict

from ..data.library_images import inspect_images
from ..data.plan_contract import plan_v4_schema, plan_v5_schema
from ..domain.catalog import ExerciseReference, content_sha256
from ..domain.execution_modes import upgrade_payload
from ..domain.group_plans import (
    diff_plans,
    identity_rows,
    plan_actions,
    revision_code_for_change,
    validate_plan_payload,
    validate_stored_plan,
)
from ..domain.plan_editing import PlanIssue, PlanIssues, compile_input, payload_issues, rule_issue
from .library_workflow import LibraryTarget


class GroupPlanService:
    def __init__(self, repository, library):
        self.repository, self.library = repository, library
        self.schema = plan_v5_schema()

    def list_plans(self):
        return self.repository.list_plans() + [
            {"id": doc["id"], "active_revision_id": None}
            for doc in self.repository.edit_documents() if doc["revision_id"] is None
        ]

    def active_revisions(self):
        return [self.get(plan["active_revision_id"]) for plan in self.list_plans()
                if plan["active_revision_id"] is not None]

    def revisions(self, plan_id):
        if isinstance(plan_id, str):
            return [self.get(plan_id)]
        return [self.get(row["id"]) for row in self.repository.revisions(plan_id)]

    def get(self, revision_id):
        document = (self.repository.edit_document(revision_id) if isinstance(revision_id, str)
                    else self.repository.document_for_revision(revision_id))
        if document is None:
            return self.repository.get(revision_id)
        linked = (self.repository.get(document["revision_id"])
                  if document["revision_id"] is not None else {})
        return {**linked, "id": document["id"], "edit_document": document,
                "normalized_revision_id": document["revision_id"],
                "plan_id": linked.get("plan_id", document["id"]),
                "status": "draft", "edit_token": document["edit_token"],
                "upgrade_source_revision_id": (document["source_revision_id"]
                    if document["purpose"] == "upgrade" else None),
                "base_number": linked.get("base_number"),
                "plan_code": linked.get("plan_code"),
                "name": document["payload"]["plan"]["name"],
                "payload": deepcopy(document["payload"]), "pins": []}

    def input_issues(self, payload, *, stored=None, activation=False, raw=False):
        candidate, issues = compile_input(payload) if raw else (deepcopy(payload), [])
        # Stored migration bindings are validated through their original projection.
        if stored and stored.get("migration"):
            try:
                self.validate(candidate, stored=stored, activation=activation)
            except (ValueError, TypeError, KeyError) as exc:
                issues.append(PlanIssue("rule", detail=str(exc)))
            return candidate, issues
        invalid_numbers = {issue.path for issue in issues}
        validation_issues = payload_issues(candidate, self.schema, activation=activation)
        issues.extend(issue for issue in validation_issues if issue.path not in invalid_numbers)
        if isinstance(candidate, dict) and isinstance(candidate.get("plan"), dict) \
                and isinstance(candidate["plan"].get("days"), list):
            # Schema-valid nodes can be checked independently against exact library facts.
            for d, day in enumerate(candidate["plan"]["days"]):
                if not isinstance(day, dict) or not isinstance(day.get("items"), list):
                    continue
                for i, item in enumerate(day["items"]):
                    if not isinstance(item, dict) or not isinstance(item.get("members", []), list):
                        continue
                    for m, action in enumerate(item.get("members", [item])):
                        path = ("plan", "days", d, "items", i)
                        if item.get("kind") == "group":
                            path += ("members", m)
                        if not isinstance(action, dict) or any(
                            issue.path[:len(path)] == path for issue in issues
                        ):
                            continue
                        try:
                            reference = ExerciseReference(**action["exercise"])
                            entry = self.library.resolve(reference, action["exercise_name"],
                                                         action["content"])
                            if entry["content"]["classification"] != action["classification"]:
                                raise ValueError(
                                    "Plan classification does not match the exact content revision."
                                )
                        except (ValueError, TypeError, KeyError) as exc:
                            issues.append(PlanIssue("rule", path, action["item_id"], str(exc)))
        return candidate, issues

    def _document_target(self, payload, purpose, source_id, base, stored=None):
        """Check conversion identities without reserving a number for incomplete input."""
        self.repository.check_source(payload.get("source", {}))
        base = self._base_number(base)
        if purpose == "clone" and stored and base is not None and base != stored["base_number"]:
            raise ValueError("此草稿已分配正式基础编号，后续编辑不能更改该编号。")
        if purpose == "upgrade":
            source = self.repository.get(source_id)
            active = self.repository.active(source["plan_id"])
            if not active or active["id"] != source_id:
                raise ValueError("The active plan changed; reopen the upgrade draft.")
            payload["intent"] = "upgrade"
            payload["target_base_number"] = source["base_number"]
            self._lineage(source["plan_id"], payload)
            code, _ = revision_code_for_change(source["base_number"], source["plan_code"],
                                               source["payload"]["plan"], payload["plan"])
            return source["plan_id"], code
        if stored:
            self._lineage(stored["plan_id"], payload)
        existing = self.repository.find_plan(payload["plan"]["name"])
        if existing is not None and (not stored or existing != stored["plan_id"]):
            raise ValueError("A plan with this name already exists.")
        if not stored and base is not None and self.repository.find_base_number(base) is not None:
            raise ValueError("That plan base number is already in use.")
        if not stored and base is None and len(self.repository.list_plans()) >= 999:
            raise ValueError("All plan base numbers 001–999 are in use.")
        return (stored["plan_id"], stored["plan_code"]) if stored else (None, None)

    @staticmethod
    def _base_number(raw):
        if raw is None or (isinstance(raw, str) and not raw.strip()):
            return None
        if isinstance(raw, str) and raw.strip().isascii() and raw.strip().isdigit():
            raw = int(raw.strip())
        if type(raw) is not int or not 1 <= raw <= 999:
            raise ValueError("A plan base number must be between 001 and 999.")
        return raw

    def preview_document(self, payload, *, revision=None, purpose="new", source_id=None, base=None):
        stored = None
        if revision:
            doc = revision.get("edit_document")
            linked = doc["revision_id"] if doc else revision["id"]
            stored = self.repository.get(linked) if linked is not None else None
            if doc:
                purpose, source_id = doc["purpose"], doc["source_revision_id"]
            elif stored and stored["upgrade_source_revision_id"]:
                purpose, source_id = "upgrade", stored["upgrade_source_revision_id"]
        candidate, issues = self.input_issues(payload, raw=True, stored=stored)
        code = None
        if not issues:
            try:
                _plan_id, code = self._document_target(candidate, purpose, source_id, base, stored)
                if code is None:
                    number = self._base_number(base)
                    if number is None:
                        used = {row["base_number"] for row in self.repository.list_plans()}
                        number = next((n for n in range(1, 1000) if n not in used), None)
                    if number is None:
                        raise ValueError("All plan base numbers 001–999 are in use.")
                    code = f"plan-{number:03d}.01.00"
            except ValueError as exc:
                issues.append(rule_issue(exc, (), None, {}))
        return {"issues": issues, "plan_code": code}

    def save_document(self, payload, *, identifier=None, expected_token=None, purpose="new",
                      source_revision_id=None, requested_base_number=None):
        """Save raw input and, if complete, its normalized snapshot in one transaction."""
        with self.library._action():
            stored = None
            linked = None
            if identifier is not None:
                current = self.get(identifier)
                if current["status"] != "draft":
                    raise ValueError("Only draft revisions can be edited.")
                if current["edit_token"] != expected_token:
                    raise ValueError("The displayed plan revision changed.")
                doc = current.get("edit_document")
                if doc:
                    purpose = doc["purpose"]
                    source_revision_id = doc["source_revision_id"]
                    if purpose != "clone":
                        requested_base_number = doc["requested_base_number"]
                    linked = doc["revision_id"]
                else:
                    linked = current["id"]
                    source_revision_id = current["upgrade_source_revision_id"]
                    purpose = "upgrade" if source_revision_id else "edit"
                    identifier = None
                stored = self.repository.get(linked) if linked is not None else None
            if purpose == "upgrade":
                source = self.repository.get(source_revision_id)
                if source["status"] != "active":
                    # Content incompleteness is permitted; identity misuse is not.
                    raise ValueError("Only the latest active revision can be upgraded.")
                for other in self.repository.edit_documents():
                    if (other["purpose"] == "upgrade"
                            and other["source_revision_id"] == source_revision_id
                            and other["id"] != identifier):
                        raise ValueError("An upgrade draft already exists; reopen it to continue.")
                existing = self.repository.upgrade_draft(source["plan_id"], source_revision_id)
                if existing and existing["id"] != linked:
                    raise ValueError("An upgrade draft already exists; reopen it to continue.")
            candidate, issues = self.input_issues(payload, raw=True, stored=stored)
            target = (None, None)
            if not issues:
                try:
                    target = self._document_target(candidate, purpose, source_revision_id,
                                                   requested_base_number, stored)
                except ValueError as exc:
                    issues.append(rule_issue(exc, (), None, {}))
            now = self.library.clock.now().isoformat()
            identifier = self.repository.put_document(
                payload, now, identifier=identifier, expected_token=expected_token,
                purpose=purpose, revision_id=linked, source_revision_id=source_revision_id,
                requested_base_number=requested_base_number,
            )
            if not issues:
                plan_id, code = target
                if linked is None:
                    linked = self.repository.create(
                        candidate, now, plan_id,
                        base_number=self._base_number(requested_base_number),
                        plan_code=code, change_description=candidate.get("change_description", ""),
                        upgrade_source_revision_id=(source_revision_id
                            if purpose == "upgrade" else None),
                    )
                    self.repository.link_document(identifier, linked)
                else:
                    self.repository.replace(linked, candidate, stored["edit_token"],
                                            plan_code=code,
                                            change_description=candidate.get(
                                                "change_description", ""))
            return {"id": identifier, "issues": issues, "revision_id": linked}

    def ready_revision(self, identifier, *, activation=False):
        revision = self.get(identifier)
        doc = revision.get("edit_document")
        if doc is None:
            return revision
        linked = doc["revision_id"]
        stored = self.repository.get(linked) if linked is not None else None
        candidate, issues = self.input_issues(doc["payload"], raw=True, stored=stored,
                                             activation=activation)
        if not issues:
            try:
                self._document_target(candidate, doc["purpose"], doc["source_revision_id"],
                                      doc["requested_base_number"], stored)
            except ValueError as exc:
                issues.append(rule_issue(exc, (), None, {}))
        if issues:
            raise PlanIssues(issues)
        if stored is None or stored["payload"]["plan"] != candidate["plan"]:
            raise ValueError("请先保存最新草稿，再预览或导出。")
        return {**stored, "editing_identifier": doc["id"],
                "document_token": doc["edit_token"]}

    def delete_draft(self, identifier, expected_token):
        with self.library._action():
            revision = self.get(identifier)
            if revision["status"] != "draft" or revision["edit_token"] != expected_token:
                raise ValueError("草稿状态已变化，请重新打开后继续。")
            doc = revision.get("edit_document")
            if doc:
                self.repository.delete_document(doc["id"], expected_token)
                if doc["revision_id"] is not None:
                    self.repository.delete_draft_revision(doc["revision_id"])
            else:
                self.repository.delete_draft_revision(identifier)

    def action_content(self, action):
        """Read the exact prescription content, including retained/removed content."""
        target = LibraryTarget(ExerciseReference(**action["exercise"]), action["content"])
        return self.library.target_entry(target)

    def action_image(self, action, index):
        entry = self.action_content(action)
        image = entry["content"]["guidance"]["images"][index]
        data = self.library._read_image(entry, image)
        if not inspect_images([image], lambda _: data)[0].valid:
            raise ValueError("Image is unavailable or invalid.")
        return data

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
        schema = plan_v4_schema() if payload.get("schema_version") == 4 else self.schema
        if payload.get("schema_version") == 4 and stored is None:
            raise ValueError("Only plan format version 5 is accepted.")
        validated = (validate_plan_payload(payload, schema, activation=activation)
                     if stored is None else validate_stored_plan(payload, schema, {
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

    def create(self, payload, *, plan_id=None, base_number=None, change_description=None):
        if plan_id is not None:
            raise ValueError("Use an explicit Upgrade to add a revision to an existing plan.")
        with self.library._action():
            payload = self.validate(payload)
            self.repository.check_source(payload.get("source", {}))
            self._lineage(plan_id, payload)
            name = payload["plan"]["name"]
            if self.repository.find_plan(name) is not None and plan_id is None:
                raise ValueError("A plan with this name already exists.")
            if (
                base_number is not None
                and self.repository.find_base_number(base_number) is not None
            ):
                raise ValueError("That plan base number is already in use.")
            description = (
                payload.get("change_description", "")
                if change_description is None else change_description
            )
            return self.repository.create(
                payload,
                self.library.clock.now().isoformat(),
                plan_id,
                base_number=base_number,
                change_description=description,
            )

    def save(self, revision_id, payload, *, expected_token):
        with self.library._action():
            if isinstance(revision_id, str) or self.repository.document_for_revision(revision_id):
                raise ValueError("此计划有独立编辑草稿，请重新打开最新草稿保存。")
            current = self.get(revision_id)
            payload = self.validate(payload, stored=current)
            self.repository.check_source(payload.get("source", {}))
            self._lineage(current["plan_id"], payload)
            code = None
            if current["upgrade_source_revision_id"] is not None:
                source = self.get(current["upgrade_source_revision_id"])
                active = self.repository.active(current["plan_id"])
                if active is None or active["id"] != source["id"]:
                    raise ValueError("The active plan changed; reopen the upgrade draft.")
                code, _changes = revision_code_for_change(
                    current["base_number"], source["plan_code"],
                    source["payload"]["plan"], payload["plan"],
                )
            self.repository.replace(
                revision_id,
                payload,
                expected_token,
                plan_code=code,
                change_description=payload.get("change_description", ""),
            )

    def clone(self, revision_id, *, base_number=None, name=None, change_description="",
              payload=None):
        if base_number is None or name is None or not name.strip():
            raise ValueError("A distinct plan name and unused base number are required.")
        with self.library._action():
            source = self.get(revision_id)
            payload = upgrade_payload(source["payload"] if payload is None else payload)
            payload["intent"] = "new"
            payload.pop("target_base_number", None)
            payload["plan"]["name"] = name
            payload["change_description"] = change_description
            payload = self.validate(payload)
            if self.repository.find_base_number(base_number) is not None:
                raise ValueError("That plan base number is already in use.")
            if self.repository.find_plan(name) is not None:
                raise ValueError("A plan with this name already exists.")
            return self.repository.create(
                payload,
                self.library.clock.now().isoformat(),
                base_number=base_number,
                plan_code=f"plan-{base_number:03d}.01.00",
                change_description=change_description,
            )

    def upgrade_draft(self, revision_id):
        source = self.get(revision_id)
        active = self.repository.active(source["plan_id"])
        if active is None or active["id"] != source["id"]:
            raise ValueError("Only the latest active revision can be upgraded.")
        for doc in self.repository.edit_documents():
            if doc["purpose"] == "upgrade" and doc["source_revision_id"] == source["id"]:
                return self.get(doc["id"])
        existing = self.repository.upgrade_draft(source["plan_id"], source["id"])
        return existing

    def create_upgrade(self, revision_id, payload):
        with self.library._action():
            source = self.get(revision_id)
            active = self.repository.active(source["plan_id"])
            if active is None or active["id"] != source["id"]:
                raise ValueError("Only the latest active revision can be upgraded.")
            existing = self.upgrade_draft(source["id"])
            if existing is not None:
                raise ValueError("An upgrade draft already exists; reopen it to continue.")
            payload = deepcopy(payload)
            payload["intent"] = "upgrade"
            payload["target_base_number"] = source["base_number"]
            payload = self.validate(payload)
            if payload["target_base_number"] != source["base_number"]:
                raise ValueError("The upgrade target base code does not match the selected plan.")
            self.repository.check_source(payload.get("source", {}))
            code, _changes = revision_code_for_change(
                source["base_number"], source["plan_code"],
                source["payload"]["plan"], payload["plan"],
            )
            return self.repository.create(
                payload,
                self.library.clock.now().isoformat(),
                source["plan_id"],
                plan_code=code,
                change_description=payload.get("change_description", ""),
                upgrade_source_revision_id=source["id"],
            )

    def preview_upgrade(self, revision_id, payload):
        source = self.get(revision_id)
        active = self.repository.active(source["plan_id"])
        if active is None or active["id"] != source["id"]:
            raise ValueError("Only the latest active revision can be upgraded.")
        payload = deepcopy(payload)
        payload["intent"] = "upgrade"
        payload["target_base_number"] = source["base_number"]
        payload = self.validate(payload)
        code, changes = revision_code_for_change(
            source["base_number"], source["plan_code"],
            source["payload"]["plan"], payload["plan"],
        )
        return {"plan_code": code, "changes": changes}

    def _targets(self, payload):
        return [
            LibraryTarget(ExerciseReference(**action["exercise"]), action["content"])
            for _day, _item, action in plan_actions(payload["plan"])
        ]

    def preview(self, revision_id):
        revision = self.ready_revision(revision_id, activation=True)
        if revision["status"] != "draft":
            raise ValueError("Only draft revisions can be activated.")
        payload = self.validate(revision["payload"], activation=True, stored=revision)
        content_issues = {issue["item_id"]: issue for issue in self.content_issues(revision_id)}
        issues = []
        for d, day in enumerate(payload["plan"]["days"]):
            for i, item in enumerate(day["items"]):
                for m, action in enumerate(item.get("members", [item])):
                    issue = content_issues.get(action["item_id"])
                    if issue:
                        path = ("plan", "days", d, "items", i)
                        if item["kind"] == "group":
                            path += ("members", m)
                        issues.extend(PlanIssue("content." + reason, path,
                                                action["item_id"], action["exercise_name"])
                                      for reason in issue["reasons"])
        if issues:
            raise PlanIssues(issues)
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
            revision_id = preview["revision"]["id"]
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
            doc_id = preview["revision"].get("editing_identifier")
            if doc_id:
                self.repository.delete_document(doc_id, preview["revision"]["document_token"])

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
