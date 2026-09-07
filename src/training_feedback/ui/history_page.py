"""训练历史页：列出训练及动作结果，展示详情并导出单次训练证据。"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
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
        self.history_list.currentItemChanged.connect(self._show_details)
        layout.addWidget(self.history_list)
        self.details = QLabel()
        self.details.setWordWrap(True)
        layout.addWidget(self.details)
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
                f"训练日期：{session['training_date']} | "
                f"{label(SESSION_STATUS_LABELS, session['status'])} | {feedback_status}"
            )
            item.setData(Qt.ItemDataRole.UserRole, session["id"])
            self.history_list.addItem(item)
            for action in session["actions"]:
                result = (
                    label(RESULT_LABELS, action["result"])
                    if action["result"]
                    else "未记录"
                )
                action_item = QListWidgetItem(
                    f"  {action['exercise_name_snapshot']} | {result}"
                )
                action_item.setData(Qt.ItemDataRole.UserRole, session["id"])
                self.history_list.addItem(action_item)
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
            planned = ", ".join(
                f"{item['planned_value']} {label(DOSE_UNIT_LABELS, item['planned_unit'])}"
                for item in action["sets"]
            )
            actual = ", ".join(
                f"{item['value']} {label(DOSE_UNIT_LABELS, item['unit'])}"
                + (" / 每侧" if item["per_side"] else "")
                for item in action.get("actual_sets", [])
            ) or "未知"
            lines.append(
                f"{action['exercise_name_snapshot']}："
                f"{label(RESULT_LABELS, action['result']) if action['result'] else '未记录'}；"
                f"计划剂量：{planned}；实际剂量：{actual}；"
                f"备注：{action.get('note') or ''}"
            )
        event_labels = {
            "pause": "暂停",
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
        self.details.setText("\n".join(lines))

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
