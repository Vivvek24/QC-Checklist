"""Batch Validation Repository — holds the batch no duplicate check SQL query."""

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


class BatchValidationRepository:
    """Infrastructure layer — raw SQL for batch+test duplicate detection."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def check_duplicate_batch_test(
        self,
        batch_question_id: int,
        test_question_id: int,
        stage_master_id: int,
        checklist_request_id: int,
        batch_values_in_clause: str,
        test_value: str,
    ) -> bool:
        """
        Port of Mendix JA_BatchNoValidation.
        Checks if another request already has the same batch+test combination.
        Returns True if a duplicate exists.
        """
        sql = f"""
SELECT EXISTS (
    SELECT 1
    FROM checklist_requests r
    JOIN checklist_stages cs ON cs.checklist_request_id = r.id
    JOIN format_stage_mappings fsm ON fsm.id = cs.format_stage_mapping_id
    JOIN stages s ON s.id = fsm.stage_id
    JOIN stage_question_mappings sqm ON sqm.format_stage_mapping_id = fsm.id
    JOIN questions q ON q.id = sqm.question_id
    JOIN question_answers qa ON qa.checklist_stage_id = cs.id AND qa.stage_question_mapping_id = sqm.id
    LEFT JOIN question_answer_sub_question_answers qasqa ON qasqa.question_answer_id = qa.id
    LEFT JOIN question_answer_helpers qah ON qah.id = qasqa.question_answer_helper_id
    WHERE q.id IN (:batch_q_id, :test_q_id)
      AND s.id = :stage_master_id
      AND r.id <> :checklist_request_id
      AND r.is_removed = false
    GROUP BY r.id
    HAVING COUNT(DISTINCT q.id) = 2
       AND BOOL_OR(
            q.id = :batch_q_id2
            AND (
                UPPER(qa.textbox_value) IN ({batch_values_in_clause})
                OR UPPER(qah.text_box_value) IN ({batch_values_in_clause})
            )
       )
       AND BOOL_OR(
            q.id = :test_q_id2
            AND UPPER(qa.textbox_value) = UPPER(:test_value)
       )
)
"""
        params = {
            "batch_q_id": batch_question_id,
            "test_q_id": test_question_id,
            "stage_master_id": stage_master_id,
            "checklist_request_id": checklist_request_id,
            "batch_q_id2": batch_question_id,
            "test_q_id2": test_question_id,
            "test_value": test_value,
        }

        result = await self._session.execute(text(sql), params)
        return result.scalar() or False
