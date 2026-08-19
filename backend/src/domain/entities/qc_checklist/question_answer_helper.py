"""QuestionAnswerHelper — domain entity."""

from dataclasses import dataclass, field

from src.domain.entities.base_entity import BaseEntity


@dataclass
class QuestionAnswerHelper(BaseEntity):
    """A helper entry linked to question answers (many-to-many via junction)."""

    text_box_value: str = field(default="")
