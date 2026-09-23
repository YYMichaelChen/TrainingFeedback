"""单次训练执行的可变状态控制器：start/resume/record/pause/abort/finish。"""

from __future__ import annotations


class GroupSessionController:
    """Own displayed occurrence and unfinished state through optimistic service commands."""

    def __init__(self, service):
        self.service = service
        self.session = None

    def start(self, revision_id, day_order, *, expected_preview, user_confirmed):
        self.session = self.service.start(revision_id, day_order,
                                          expected_preview=expected_preview,
                                          user_confirmed=user_confirmed)
        return self.session

    def resume(self, identifier=None):
        saved = self.service.active() if identifier is None else self.service.get(identifier)
        if saved is None:
            raise ValueError("No open or paused session was found.")
        self.session = self.service.resume(saved["id"], expected_version=saved["version"])
        return self.session

    def reload(self):
        self.session = self.service.get(self.session["id"])
        return self.session

    @property
    def current(self):
        return self.session["occurrences"][self.session["position"]]

    @property
    def next_occurrence(self):
        position = self.session["position"] + 1
        rows = self.session["occurrences"]
        return rows[position] if position < len(rows) else None

    @property
    def unfinished(self):
        return [row for row in self.session["occurrences"] if row["result"] is None]

    def _command(self, method, *args, **kwargs):
        self.session = method(self.session["id"], *args,
                              expected_version=self.session["version"], **kwargs)
        return self.session

    def navigate(self, position):
        return self._command(self.service.navigate, position)

    def next_unfinished(self):
        rows = self.unfinished
        if rows:
            following = next((row for row in rows if row["position"] > self.session["position"]),
                             rows[0])
            return self.navigate(following["position"])
        return self.session

    def record(self, result, *, actual=(), note=""):
        return self._command(self.service.record, self.current["id"], result,
                             actual=actual, note=note)

    def preview_round(self):
        return self.service.preview_round(self.session["id"])

    def complete_round(self, preview, *, user_confirmed):
        self.session = self.service.complete_round(self.session["id"],
                                                   expected_preview=preview["token"],
                                                   user_confirmed=user_confirmed)
        return self.session

    def retract(self, *, user_confirmed):
        row = self.current
        target = {"batch_id": row["batch_id"]} if row["batch_id"] is not None else {
            "occurrence_id": row["id"]}
        return self._command(self.service.retract, user_confirmed=user_confirmed, **target)

    def pause(self):
        return self._command(self.service.pause)

    def abort(self, reason, note, *, user_confirmed):
        return self._command(self.service.abort, reason, note, user_confirmed=user_confirmed)

    def finish(self, *, user_confirmed):
        return self._command(self.service.finish, user_confirmed=user_confirmed)
