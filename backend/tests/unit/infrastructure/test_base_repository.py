"""
Contract tests for the generic repository base classes.

These exist as the documented extension point for future code-keyed master
aggregates (see `api-layer-standard.md`); no aggregate in this service is
code-keyed yet, so nothing exercises them transitively the way a concrete
master's integration tests would. Without these tests the abstract hooks could
be quietly removed or renamed and nothing would notice until the first master
was written against a contract that no longer held.

Everything here is in-memory: `SqlAlchemyRepository`'s query methods need a real
session and belong in `tests/integration/database/` once a concrete subclass
exists. What is asserted here is the shape of the contract, not SQL behaviour.
"""

import inspect
from uuid import UUID, uuid4

import pytest
from sqlalchemy import ColumnElement

from src.domain.entities.base_entity import BaseEntity
from src.domain.repositories.base_repository import IRepository
from src.infrastructure.database.repositories.base_repository_impl import (
    SqlAlchemyRepository,
)


class TestIRepositoryContract:
    """The domain-layer port."""

    def test_cannot_be_instantiated_directly(self) -> None:
        with pytest.raises(TypeError):
            IRepository()  # type: ignore[abstract]

    def test_declares_the_full_crud_contract(self) -> None:
        # Named explicitly rather than derived, so deleting a method from the
        # port fails here instead of silently shrinking the contract.
        assert IRepository.__abstractmethods__ == frozenset(
            {
                "get_by_id",
                "get_by_code",
                "create",
                "update",
                "delete",
                "list_all",
                "count",
                "exists_by_code",
            }
        )

    def test_every_contract_method_is_async(self) -> None:
        for name in IRepository.__abstractmethods__:
            assert inspect.iscoroutinefunction(getattr(IRepository, name)), name

    def test_a_partial_implementation_still_cannot_be_instantiated(self) -> None:
        class OnlyGetById(IRepository[BaseEntity]):
            async def get_by_id(self, entity_id: UUID) -> BaseEntity | None:
                return None

        with pytest.raises(TypeError):
            OnlyGetById()  # type: ignore[abstract]

    def test_is_generic_over_its_entity(self) -> None:
        # Subscripting must work; a plain ABC would raise here.
        assert IRepository[BaseEntity] is not None


class TestSqlAlchemyRepositoryContract:
    """The infrastructure-layer shared mechanics."""

    def test_requires_the_two_mapping_hooks(self) -> None:
        # These are the only things a subclass must supply; if either stops being
        # abstract, subclasses would silently inherit a broken default.
        assert SqlAlchemyRepository.__abstractmethods__ == frozenset(
            {"_to_entity", "_code_equals"}
        )

    def test_cannot_be_instantiated_without_the_hooks(self) -> None:
        with pytest.raises(TypeError):
            SqlAlchemyRepository(session=None)  # type: ignore[abstract,arg-type]

    def test_provides_the_shared_crud_mechanics_concretely(self) -> None:
        # The point of the base class: these are inherited, not reimplemented.
        for name in ("get_by_id", "get_by_code", "exists_by_code", "delete"):
            assert name not in SqlAlchemyRepository.__abstractmethods__
            assert inspect.iscoroutinefunction(getattr(SqlAlchemyRepository, name))

    def test_exposes_the_internal_model_loaders_for_subclasses(self) -> None:
        for name in ("_get_model", "_require_model"):
            assert inspect.iscoroutinefunction(getattr(SqlAlchemyRepository, name))

    def test_a_complete_subclass_binds_its_session(self) -> None:
        repo = _FakeRepository(session=None)  # type: ignore[arg-type]

        # Constructing it at all proves both hooks satisfied the ABC.
        assert repo._model is _StubModel

    async def test_require_model_raises_when_the_row_is_gone(self) -> None:
        repo = _FakeRepository(session=None)  # type: ignore[arg-type]
        missing = uuid4()

        with pytest.raises(ValueError, match=str(missing)):
            await repo._require_model(missing)


# ─── Test doubles ───
# A minimal subclass, not a real model/entity: enough to prove the ABC is
# satisfiable and that _require_model's not-found path reports the id.


class _StubModel:
    __name__ = "_StubModel"


class _FakeRepository(SqlAlchemyRepository[BaseEntity, _StubModel]):  # type: ignore[type-var]
    _model = _StubModel

    @staticmethod
    def _to_entity(model: _StubModel) -> BaseEntity:
        return BaseEntity()

    @staticmethod
    def _code_equals(code: str) -> ColumnElement[bool]:
        raise NotImplementedError("not needed for contract tests")

    async def _get_model(self, entity_id: UUID) -> _StubModel | None:
        # Overridden so the not-found path is reachable without a live session.
        return None
