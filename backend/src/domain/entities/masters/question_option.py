"""QuestionOption Master — domain entity."""

from dataclasses import dataclass, field

from src.domain.entities.base_entity import BaseEntity


@dataclass
class QuestionOption(BaseEntity):
    """Option associated with a Question master."""

    option_title: str = field(default="")
    is_response_option: bool = field(default=False)
    question_id: int = field(default=0)
    is_active: bool = field(default=True)
