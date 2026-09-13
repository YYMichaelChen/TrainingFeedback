"""训练历史页：列出训练及动作结果，展示详情并导出单次训练证据。"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from ..data.handoff import HandoffError, HandoffService
from .labels import (
    DOSE_UNIT_LABELS,
    FEEDBACK_VALUE_LABELS,
    RESULT_LABELS,
    SESSION_STATUS_LABELS,
    label,
    session_prescription_text,
    user_message,
)


class HistoryPage(QWidget):
    """训练历史页：按时间倒序展示会话及其动作结果。"""
    def __init__(self, context, parent=None):
        super().__init__(parent)
        self.context = context
        self.service = context.feedback_service()
        self.sessions_by_id = {}
        layout = QVBoxLayout(self)
        title = QLabel("训练历史")
        title.setObjectName("pageTitle")
        layout.addWidget(title)
        self.history_list = QListWidget()
        self.history_list.setMinimumWidth(210)
        self.history_list.setWordWrap(True)
        self.history_list.currentItemChanged.connect(self._show_details)
        self.details = QPlainTextEdit()
        self.details.setReadOnly(True)
        splitter = QSplitter()
        splitter.addWidget(self.history_list)
        splitter.addWidget(self.details)
        splitter.setSizes([240, 560])
        splitter.setStretchFactor(1, 1)
        layout.addWidget(splitter, 1)
        self.export_button = QPushButton("导出所选训练证据")
        self.export_button.clicked.connect(self._export_selected)
        layout.addWidget(self.export_button)
        self.refresh()

    def refresh(self) -> None:
        self.history_list.clear()
        sessions = self.service.history()
        self.sessions_by_id = {session["id"]: session for session in sessions}
        for session in sessions:
            feedback = session["feedback"]
            feedback_status = "已提交反馈" if feedback else "尚未填写反馈"
            item = QListWidgetItem(
                f"{session['training_date']}\n"
                f"{label(SESSION_STATUS_LABELS, session['status'])} · {feedback_status}"
            )
            item.setData(Qt.ItemDataRole.UserRole, session["id"])
            self.history_list.addItem(item)
        if self.history_list.count():
            self.history_list.setCurrentRow(0)

    def _show_details(self, current, _previous) -> None:
        if current is None:
            self.details.clear()
            return
        session_id = current.data(Qt.ItemDataRole.UserRole)
        if session_id is None:
            return
        session = self.sessions_by_id.get(session_id)
        if session is None:
            return
        lines = [
            f"训练日期：{session['training_date']}",
            f"状态：{label(SESSION_STATUS_LABELS, session['status'])}",
            f"计划版本：{session['plan_revision_id']}",
            "训练动作：",
        ]
        for action in session["actions"]:
            planned = session_prescription_text(action)
            actual = ", ".join(
                f"{item['value']} {label(DOSE_UNIT_LABELS, item['unit'])}"
                + (" / 每侧" if item["per_side"] else "")
                for item in action.get("actual_sets", [])
            ) or ("按计划完成（未另填实际剂量）" if action["result"] == "completed" else "未填写")
            lines.append(
                f"{action['exercise_name_snapshot']}："
                f"{label(RESULT_LABELS, action['result']) if action['result'] else '未记录'}；"
                f"计划剂量：{planned}；实际剂量：{actual}；"
                f"备注：{action.get('note') or ''}"
            )
        for audit in session.get("result_retractions", []):
            previous = audit["previous_action"]
            prior_dose = "、".join(
                f"{item['value']:g} {label(DOSE_UNIT_LABELS, item['unit'])}"
                + (" / 每侧" if item["per_side"] else "")
                for item in previous.get("actual_sets", [])
            ) or "未另填"
            lines.append(
                f"\n结果撤回 · {audit['retracted_at']}\n"
                f"{previous['exercise_name_snapshot']}：原结果 "
                f"{label(RESULT_LABELS, previous['result'])}；原实际剂量：{prior_dose}；"
                f"原备注：{previous.get('note') or ''}"
            )
        event_labels = {
            "pause": "暂停",
            "resume": "恢复",
            "completed": "完成",
            "partial": "部分完成",
            "aborted": "中止",
        }
        lines.append(
            "事件：" + ", ".join(
                event_labels.get(event["event_type"], event["event_type"])
                for event in session["events"]
            )
        )
        if session["feedback"]:
            feedback = session["feedback"]
            lines.append(f"反馈备注：{feedback['overall_note'] or ''}")
            for area in feedback["areas"]:
                lines.append(
                    f"{area['body_area_name_snapshot']}："
                    f"{label(FEEDBACK_VALUE_LABELS, area['value']) if area['value'] else '未回答'}"
                )
            lines.append(f"备注修正次数：{len(feedback['audit'])}")
        self.details.setPlainText("\n".join(lines))

    def _export_selected(self) -> None:
        item = self.history_list.currentItem()
        session_id = item.data(Qt.ItemDataRole.UserRole) if item is not None else None
        if session_id is None:
            QMessageBox.information(self, "没有选择", "请先选择一次训练。")
            return
        try:
            json_path, markdown_path = HandoffService(
                self.context.database.connection, self.context.data_root.path
            ).export(session_id)
        except (HandoffError, OSError) as exc:
            QMessageBox.warning(self, "导出失败", user_message(str(exc)))
            return
        QMessageBox.information(
            self,
            "导出完成",
            f"已导出所选训练：\n{json_path.name}\n{markdown_path.name}",
        )
