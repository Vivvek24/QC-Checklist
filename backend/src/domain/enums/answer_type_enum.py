"""Answer Type enums for the Question Master."""

from enum import StrEnum


class AnswerType(StrEnum):
    TEXT_BOX = "Text Box"
    NONE = "None"
    DROPDOWN_SINGLE = "Dropdown (single select)"
    DROPDOWN_MULTI = "Dropdown (multi select)"
    DATE_TIME = "Date & Time"
    MASTERS = "Masters"
