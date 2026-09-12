"""
Integration tests for the published POST /adintegratorservices/rest/v1/validatecredentials.

Focus: the shared-key encryption layer added over the endpoint. A consuming app
encrypts EmployeeId + Password with the Fernet key; this service decrypts them
before the LDAP bind. The LDAP call itself is faked — these assert the crypto
boundary and the legacy response contract, not LDAP behaviour.

Dependencies are swapped via `app.dependency_overrides`, per the note in
`test_auth_api.py`: patching module attributes has no effect on an already-declared
route, but the override registry does (and reaches nested dependencies too).
"""

from typing import Any

import pytest
from cryptography.fernet import Fernet
from httpx import AsyncClient

from src.api.v1.dependencies import get_credential_cipher
from src.api.v1.endpoints import darwin_ad_controller
from src.infrastructure.security.credential_cipher_impl import (
    FernetCredentialCipher,
    PassthroughCredentialCipher,
)
from src.main import app

ENDPOINT = "/adintegratorservices/rest/v1/validatecredentials"


class _FakeLdapService:
    """
    Stand-in for LdapService that records what it was asked to validate and
    returns a scripted `validate_credentials_across_servers` result.

    The recorded (username, password) is the assertion hook: it proves the
    controller handed LDAP the *decrypted* values, not the ciphertext.
    """

    def __init__(self, result: dict[str, Any]) -> None:
        self._result = result
        self.seen: tuple[str, str] | None = None

    async def validate_credentials_across_servers(
        self, username: str, password: str
    ) -> dict[str, Any]:
        self.seen = (username, password)
        return self._result


def _valid_result(server: str = "Emcure Pharma") -> dict[str, Any]:
    return {
        "is_success": True,
        "is_valid_user": True,
        "raw_response": {"matched_server": server},
    }


def _invalid_result() -> dict[str, Any]:
    return {
        "is_success": True,
        "is_valid_user": False,
        "raw_response": {},
    }


@pytest.fixture
def key() -> str:
    return Fernet.generate_key().decode("utf-8")


@pytest.fixture(autouse=True)
def _clear_overrides() -> Any:
    """Each test wires its own overrides; never leak them into the next."""
    yield
    app.dependency_overrides.pop(get_credential_cipher, None)
    app.dependency_overrides.pop(darwin_ad_controller._get_ldap_service, None)


def _use_ldap(result: dict[str, Any]) -> _FakeLdapService:
    fake = _FakeLdapService(result)
    app.dependency_overrides[darwin_ad_controller._get_ldap_service] = lambda: fake
    return fake


class TestEncryptedInputs:
    """Key configured: EmployeeId + Password arrive as Fernet tokens."""

    async def test_valid_tokens_are_decrypted_and_validated(
        self, client: AsyncClient, key: str
    ) -> None:
        app.dependency_overrides[get_credential_cipher] = lambda: FernetCredentialCipher(key)
        ldap = _use_ldap(_valid_result(server="Emcure Pharma"))
        f = Fernet(key.encode())

        response = await client.post(
            ENDPOINT,
            data={
                "EmployeeId": f.encrypt(b"93300116").decode(),
                "Password": f.encrypt(b"s3cret").decode(),
            },
        )

        assert response.status_code == 200, response.text
        body = response.json()
        assert body["IsSuccess"] is True
        assert body["IsValidUser"] is True
        assert "Emcure Pharma" in body["Message"]
        # The bind saw plaintext, not ciphertext — the whole point of the layer.
        assert ldap.seen == ("93300116", "s3cret")

    async def test_valid_tokens_but_ldap_rejects(
        self, client: AsyncClient, key: str
    ) -> None:
        app.dependency_overrides[get_credential_cipher] = lambda: FernetCredentialCipher(key)
        _use_ldap(_invalid_result())
        f = Fernet(key.encode())

        response = await client.post(
            ENDPOINT,
            data={
                "EmployeeId": f.encrypt(b"93300116").decode(),
                "Password": f.encrypt(b"wrong").decode(),
            },
        )

        assert response.status_code == 200, response.text
        body = response.json()
        assert body["IsSuccess"] is True
        assert body["IsValidUser"] is False
        assert body["Message"] == "Invalid username or password"

    async def test_a_bad_token_never_reaches_ldap_and_reports_invalid(
        self, client: AsyncClient, key: str
    ) -> None:
        app.dependency_overrides[get_credential_cipher] = lambda: FernetCredentialCipher(key)
        ldap = _use_ldap(_valid_result())  # would say "valid" if it were ever called

        response = await client.post(
            ENDPOINT,
            # Plaintext where a token is required, i.e. an unencrypted / wrong-key caller.
            data={"EmployeeId": "93300116", "Password": "s3cret"},
        )

        assert response.status_code == 200, response.text
        body = response.json()
        assert body["IsValidUser"] is False
        assert body["Message"] == "Invalid username or password"
        # Critical: a bad token must short-circuit before the LDAP bind.
        assert ldap.seen is None

    async def test_a_token_from_a_different_key_is_rejected(
        self, client: AsyncClient, key: str
    ) -> None:
        app.dependency_overrides[get_credential_cipher] = lambda: FernetCredentialCipher(key)
        ldap = _use_ldap(_valid_result())
        foreign = Fernet(Fernet.generate_key())

        response = await client.post(
            ENDPOINT,
            data={
                "EmployeeId": foreign.encrypt(b"93300116").decode(),
                "Password": foreign.encrypt(b"s3cret").decode(),
            },
        )

        assert response.status_code == 200, response.text
        assert response.json()["IsValidUser"] is False
        assert ldap.seen is None


class TestPlaintextWhenKeyUnset:
    """No key configured: the cipher is a passthrough, preserving drop-in behaviour."""

    async def test_plaintext_inputs_are_validated_directly(
        self, client: AsyncClient
    ) -> None:
        app.dependency_overrides[get_credential_cipher] = PassthroughCredentialCipher
        ldap = _use_ldap(_valid_result(server="Legacy"))

        response = await client.post(
            ENDPOINT,
            data={"EmployeeId": "93300116", "Password": "s3cret"},
        )

        assert response.status_code == 200, response.text
        body = response.json()
        assert body["IsValidUser"] is True
        assert ldap.seen == ("93300116", "s3cret")


class TestContractUnchanged:
    """The request/response shape must still match the legacy Mendix service."""

    async def test_missing_form_fields_return_422(self, client: AsyncClient) -> None:
        app.dependency_overrides[get_credential_cipher] = PassthroughCredentialCipher
        _use_ldap(_valid_result())

        response = await client.post(ENDPOINT, data={})

        assert response.status_code == 422, response.text

    async def test_response_has_exactly_the_legacy_keys(
        self, client: AsyncClient
    ) -> None:
        app.dependency_overrides[get_credential_cipher] = PassthroughCredentialCipher
        _use_ldap(_valid_result())

        response = await client.post(
            ENDPOINT, data={"EmployeeId": "x", "Password": "y"}
        )

        assert set(response.json().keys()) == {"IsSuccess", "Message", "IsValidUser"}
