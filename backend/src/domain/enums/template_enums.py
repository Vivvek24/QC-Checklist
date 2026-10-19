"""Template (checklist column design) enums."""

from enum import StrEnum


class ColumnType(StrEnum):
    """How a checklist template column renders/behaves.

    - SERIAL    -> auto Sr No (row index)
    - QUESTION  -> a question picked from the question master
    - OPTION    -> select option (auto-populated from the row's picked question)
    - ANSWER    -> enter answer; branches on the question's answer_type
    - RESPONSE  -> YES / NO / N-A radio group (Chromatographic response)
    - RESPONSE_QUESTION_OPTION -> a dropdown populated from the row's question's
      response options (its response_options), stored as response_question_option_id
    - AQL_LIMIT -> AQL limit (auto from the row's picked question, or a
      row-level override)
    """

    SERIAL = "SERIAL"
    QUESTION = "QUESTION"
    OPTION = "OPTION"
    ANSWER = "ANSWER"
    RESPONSE = "RESPONSE"
    RESPONSE_QUESTION_OPTION = "RESPONSE_QUESTION_OPTION"
    AQL_LIMIT = "AQL_LIMIT"
