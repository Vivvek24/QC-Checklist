"""User details repository interface (Port)."""

from abc import ABC, abstractmethod

from src.domain.entities.user_details import UserDetails


class IUserDetailsRepository(ABC):

    @abstractmethod
    async def get_by_user_id(self, user_id: int) -> UserDetails | None: ...

    @abstractmethod
    async def get_many_by_user_ids(
        self, user_ids: list[int]
    ) -> dict[int, UserDetails]: ...

    @abstractmethod
    async def upsert_email(self, user_id: int, email: str, modified_by: str) -> None:
        """Create or update the email field on user_details for a given user."""
        ...
