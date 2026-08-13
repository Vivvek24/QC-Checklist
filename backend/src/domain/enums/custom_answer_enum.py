"""CustomAnswer enum for StageQuestionMapping."""

from enum import StrEnum


class CustomAnswer(StrEnum):
    START_DATE = "StartDate"
    END_DATE = "EndDate"
    CALCULATE_SAMPLE_DESTROYED = "Calculate_SampleDestroyed"
    CALCULATE_SAMPLE_CONSUMED = "Calculate_SampleConsumed"
