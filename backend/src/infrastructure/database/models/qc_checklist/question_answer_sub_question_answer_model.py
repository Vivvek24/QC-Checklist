"""QuestionAnswer self-join — parent QuestionAnswer ↔ child (sub) QuestionAnswer.

Mirrors the Mendix self-association on QuestionAnswer: a question's
sub-question answers are themselves QuestionAnswer rows, linked to the parent
answer through this junction. Both columns reference question_answers.id —
`question_answer_id` is the child (sub) answer, `question_answer_parent_id` is
the parent answer it belongs to.
"""

from sqlalchemy import BigInteger, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from src.infrastructure.database.models.base_model import BaseModel


class QuestionAnswerSubQuestionAnswerModel(BaseModel):
    __tablename__ = "question_answer_sub_question_answers"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True, nullable=False)
    question_answer_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("question_answers.id", ondelete="CASCADE"), nullable=False, index=True
    )
    question_answer_parent_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("question_answers.id", ondelete="CASCADE"), nullable=False, index=True
    )
