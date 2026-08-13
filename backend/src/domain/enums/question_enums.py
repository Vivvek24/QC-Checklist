"""Question Master enums."""

from enum import StrEnum


class AnswerType(StrEnum):
    TEXT_BOX = "Text Box"
    NONE = "None"
    DROPDOWN_SINGLE = "Dropdown (single select)"
    DROPDOWN_MULTI = "Dropdown (multi select)"
    DATE_AND_TIME = "Date and Time"
