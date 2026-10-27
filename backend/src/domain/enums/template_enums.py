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
    - TEST_TITLE -> the auto-generated test name for the row (question_answer
      test_title), produced when a Masters/Product answer expands into per-test
      rows; rendered read-only
    - SAMPLE_VIAL -> the sample vial value for the row (question_answer
      sample_vails); entered at fill time
    - ISSUE_VIALS -> an "Issue Vials" action button; records the issue
      date/issuer on the row's question_answer (issued_by_date / issuer_name)
    - RECEIVE_VIALS -> receive-vials column (fill-time rendering TBD)
    - AQL_LIMIT -> AQL limit (auto from the row's picked question, or a
      row-level override)
    """

    SERIAL = "SERIAL"
    QUESTION = "QUESTION"
    OPTION = "OPTION"
    ANSWER = "ANSWER"
    RESPONSE = "RESPONSE"
    RESPONSE_QUESTION_OPTION = "RESPONSE_QUESTION_OPTION"
    TEST_TITLE = "TEST_TITLE"
    SAMPLE_VIAL = "SAMPLE_VIAL"
    ISSUE_VIALS = "ISSUE_VAILS"
    RECEIVE_VIALS = "RECEIVE_VIALS"
    AQL_LIMIT = "AQL_LIMIT"
