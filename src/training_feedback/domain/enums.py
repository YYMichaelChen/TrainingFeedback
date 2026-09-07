"""全局受控枚举：剂量单位、动作结果、会话状态、中止原因、反馈取值。取值入库，新增时勿改已有值。"""

from enum import StrEnum


class DoseUnit(StrEnum):
    REPS = "reps"
    SECONDS = "seconds"
    MINUTES = "minutes"
    BREATHS = "breaths"
    FREE = "free"


class ExerciseResult(StrEnum):
    EXCEEDED = "exceeded"
    COMPLETED = "completed"
    PARTIAL = "partial"
    NOT_COMPLETED = "not_completed"


class SessionStatus(StrEnum):
    OPEN = "open"
    PAUSED = "paused"
    COMPLETED = "completed"
    PARTIAL = "partial"
    ABORTED = "aborted"


class AbortReason(StrEnum):
    DISCOMFORT = "discomfort"
    PAIN_OR_INJURY = "pain_or_injury"
    URGENT_INTERRUPTION = "urgent_interruption"
    INSUFFICIENT_TIME = "insufficient_time"
    OTHER = "other"


class FeedbackValue(StrEnum):
    SIGNIFICANT_SORENESS = "significant_soreness"
    SOME_SORENESS = "some_soreness"
    NO_OBVIOUS_SENSATION = "no_obvious_sensation"
    DISCOMFORT_OR_INJURY = "discomfort_or_injury"
