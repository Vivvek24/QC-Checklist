"""
Unit tests for the two-stage request audit context.

The bug these lock down was silent: `AuditContextMiddleware` used to read
`request.state.user_id` / `.username`, which nothing ever set, so every
automatically captured audit row was attributed to "anonymous" while looking
perfectly healthy. The fix splits population into two stages — the middleware
seeds IP/user-agent before routing, and the auth dependency attaches the
resolved identity via `set_audit_actor` — so the thing worth asserting is that
stage 2 *adds* to stage 1 rather than replacing it.
"""

from uuid import uuid4

from src.infrastructure.database.audit_context import (
    clear_audit_context,
    get_audit_context,
    reset_audit_context,
    set_audit_actor,
    set_audit_context,
)


class TestDefaultContext:
    def test_defaults_to_the_system_actor(self) -> None:
        clear_audit_context()

        ctx = get_audit_context()

        # "system" (not "anonymous") is what marks writes from scripts, seeders
        # and background work that never went through a request.
        assert ctx.actor_username == "system"
        assert ctx.actor_id is None
        assert ctx.ip_address == ""


class TestSetAuditContext:
    def test_replaces_the_whole_context_and_returns_a_restore_token(self) -> None:
        token = set_audit_context(
            actor_username="anonymous", ip_address="10.0.0.1", user_agent="curl/8"
        )

        ctx = get_audit_context()
        assert ctx.actor_username == "anonymous"
        assert ctx.ip_address == "10.0.0.1"
        assert ctx.user_agent == "curl/8"

        reset_audit_context(token)

        # Restoring matters: worker tasks are reused, so without it one request's
        # actor could be read by the next.
        assert get_audit_context().actor_username == "system"

    def test_nested_contexts_restore_in_reverse_order(self) -> None:
        outer = set_audit_context(actor_username="outer", ip_address="1.1.1.1")
        inner = set_audit_context(actor_username="inner", ip_address="2.2.2.2")

        assert get_audit_context().actor_username == "inner"

        reset_audit_context(inner)
        assert get_audit_context().actor_username == "outer"
        assert get_audit_context().ip_address == "1.1.1.1"

        reset_audit_context(outer)
        assert get_audit_context().actor_username == "system"


class TestSetAuditActor:
    def test_attaches_the_identity_while_preserving_request_data(self) -> None:
        """This is the regression guard: stage 2 must not blank out stage 1."""
        token = set_audit_context(
            actor_username="anonymous", ip_address="10.0.0.1", user_agent="Firefox"
        )
        user_id = uuid4()

        set_audit_actor(actor_id=user_id, actor_username="alice")

        ctx = get_audit_context()
        assert ctx.actor_id == user_id
        assert ctx.actor_username == "alice"
        assert ctx.ip_address == "10.0.0.1"
        assert ctx.user_agent == "Firefox"

        reset_audit_context(token)

    def test_omitting_tenant_id_leaves_an_existing_one_intact(self) -> None:
        tenant = uuid4()
        token = set_audit_context(actor_username="anonymous", tenant_id=tenant)

        set_audit_actor(actor_id=uuid4(), actor_username="alice")

        assert get_audit_context().tenant_id == tenant

        reset_audit_context(token)

    def test_supplying_tenant_id_overwrites_it(self) -> None:
        token = set_audit_context(actor_username="anonymous", tenant_id=uuid4())
        new_tenant = uuid4()

        set_audit_actor(
            actor_id=uuid4(), actor_username="alice", tenant_id=new_tenant
        )

        assert get_audit_context().tenant_id == new_tenant

        reset_audit_context(token)
