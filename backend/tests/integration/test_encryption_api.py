"""
Integration tests for POST /api/v1/services/encryption/encrypt.

The endpoint is a testing helper: it turns a plaintext value into the Fernet
token the published `validatecredentials` endpoint expects, reusing the same
`get_credential_cipher` dependency. These assert the crypto boundary (the token
it returns actually decrypts back to the input with the same key), the
passthrough behaviour when no key is configured, RBAC gating, and validation.

The cipher is swapped via `app.dependency_overrides`; RBAC is exercised for real
through the `admin_client` fixture (a seeded user with `services.encryption`).
"""

from typing import Any

import pytest
from cryptography.fernet import Fernet
from httpx import AsyncClient

from src.api.v1.dependencies import get_credential_cipher
from src.infrastructure.security.credential_cipher_impl import (
    FernetCredentialCipher,
    PassthroughCredentialCipher,
)
from src.main import app

ENDPOINT = "/api/v1/services/encryption/encrypt"


@pytest.fixture
def key() -> str:
    return Fernet.generate_key().decode("utf-8")


@pytest.fixture(autouse=True)
def _clear_overrides() -> Any:
    """Each test wires its own cipher override; never leak it into the next."""
    yield
    app.dependency_overrides.pop(get_credential_cipher, None)


class TestEncryptWithKey:
    """Key configured: the returned token decrypts back to the input."""

    async def test_returns_a_token_that_round_trips(
        self, admin_client: AsyncClient, key: str
    ) -> None:
        app.dependency_overrides[get_credential_cipher] = lambda: FernetCredentialCipher(key)

        response = await admin_client.post(ENDPOINT, json={"plaintext": "Sep@2026"})

        assert response.status_code == 200, response.text
        body = response.json()
        assert body["encrypted"] is True
        # The whole point: the token must decrypt to the original plaintext.
        assert Fernet(key.encode()).decrypt(body["token"].encode()).decode() == "Sep@2026"

    async def test_token_differs_from_plaintext(
        self, admin_client: AsyncClient, key: str
    ) -> None:
        app.dependency_overrides[get_credential_cipher] = lambda: FernetCredentialCipher(key)

        response = await admin_client.post(ENDPOINT, json={"plaintext": "93300116"})

        assert response.status_code == 200, response.text
        assert response.json()["token"] != "93300116"


class TestEncryptPassthrough:
    """No key configured: plaintext is returned unchanged, encrypted=false."""

    async def test_returns_plaintext_unchanged(
        self, admin_client: AsyncClient
    ) -> None:
        app.dependency_overrides[get_credential_cipher] = PassthroughCredentialCipher

        response = await admin_client.post(ENDPOINT, json={"plaintext": "93300116"})

        assert response.status_code == 200, response.text
        body = response.json()
        assert body["token"] == "93300116"
        assert body["encrypted"] is False


class TestValidation:
    async def test_empty_plaintext_is_rejected(
        self, admin_client: AsyncClient
    ) -> None:
        app.dependency_overrides[get_credential_cipher] = PassthroughCredentialCipher

        response = await admin_client.post(ENDPOINT, json={"plaintext": ""})

        assert response.status_code == 422, response.text

    async def test_missing_plaintext_is_rejected(
        self, admin_client: AsyncClient
    ) -> None:
        app.dependency_overrides[get_credential_cipher] = PassthroughCredentialCipher

        response = await admin_client.post(ENDPOINT, json={})

        assert response.status_code == 422, response.text


class TestAuthorization:
    async def test_anonymous_caller_is_rejected(
        self, client: AsyncClient
    ) -> None:
        """No token → the require_permission gate must block before encrypting."""
        app.dependency_overrides[get_credential_cipher] = PassthroughCredentialCipher

        response = await client.post(ENDPOINT, json={"plaintext": "x"})

        assert response.status_code in (401, 403), response.text
