"""
Unit tests for the credential cipher adapters.

These back the published `validatecredentials` endpoint: a consuming app encrypts
the username and password with a shared Fernet key, and this service decrypts them
before the LDAP bind. The security-relevant behaviour is that anything which is not
a token this cipher produced with its own key fails as `CredentialDecryptError` —
never returns wrong plaintext, and never lets the caller tell *why* it failed.
"""

import pytest
from cryptography.fernet import Fernet

from src.domain.services.credential_cipher import CredentialDecryptError
from src.infrastructure.security.credential_cipher_impl import (
    FernetCredentialCipher,
    PassthroughCredentialCipher,
)


@pytest.fixture
def key() -> str:
    return Fernet.generate_key().decode("utf-8")


class TestFernetCredentialCipher:
    def test_round_trips_a_value_encrypted_with_the_same_key(self, key: str) -> None:
        token = Fernet(key.encode()).encrypt(b"93300116").decode()

        assert FernetCredentialCipher(key).decrypt(token) == "93300116"

    def test_round_trips_unicode(self, key: str) -> None:
        token = Fernet(key.encode()).encrypt("Pässwörd€".encode()).decode()

        assert FernetCredentialCipher(key).decrypt(token) == "Pässwörd€"

    def test_a_token_from_a_different_key_is_rejected(self, key: str) -> None:
        foreign = Fernet(Fernet.generate_key()).encrypt(b"secret").decode()

        with pytest.raises(CredentialDecryptError):
            FernetCredentialCipher(key).decrypt(foreign)

    def test_a_tampered_token_is_rejected(self, key: str) -> None:
        token = Fernet(key.encode()).encrypt(b"secret").decode()
        # Flip the last payload character — Fernet's HMAC must catch it.
        tampered = token[:-2] + ("A" if token[-2] != "A" else "B") + token[-1]

        with pytest.raises(CredentialDecryptError):
            FernetCredentialCipher(key).decrypt(tampered)

    def test_plain_text_that_is_not_a_token_is_rejected(self, key: str) -> None:
        with pytest.raises(CredentialDecryptError):
            FernetCredentialCipher(key).decrypt("93300116")

    def test_non_base64_input_is_rejected_as_the_same_error(self, key: str) -> None:
        """A malformed (non-base64) value raises CredentialDecryptError, not a bare ValueError."""
        with pytest.raises(CredentialDecryptError):
            FernetCredentialCipher(key).decrypt("!!! not base64 !!!")

    def test_empty_string_is_rejected(self, key: str) -> None:
        with pytest.raises(CredentialDecryptError):
            FernetCredentialCipher(key).decrypt("")

    def test_an_invalid_key_fails_at_construction_not_first_use(self) -> None:
        """A misconfigured DARWIN_VALIDATE_ENCRYPTION_KEY should fail loudly when built."""
        with pytest.raises((ValueError, TypeError)):
            FernetCredentialCipher("not-a-valid-fernet-key")


class TestFernetEncrypt:
    """The encrypt side, added for the testing-helper endpoint."""

    def test_encrypt_then_decrypt_round_trips(self, key: str) -> None:
        cipher = FernetCredentialCipher(key)

        assert cipher.decrypt(cipher.encrypt("93300116")) == "93300116"

    def test_encrypt_round_trips_unicode(self, key: str) -> None:
        cipher = FernetCredentialCipher(key)

        assert cipher.decrypt(cipher.encrypt("Pässwörd€")) == "Pässwörd€"

    def test_a_token_produced_here_is_accepted_by_the_same_key(self, key: str) -> None:
        """The endpoint's token must decrypt with the identically-configured cipher."""
        token = FernetCredentialCipher(key).encrypt("Sep@2026")

        assert Fernet(key.encode()).decrypt(token.encode()).decode() == "Sep@2026"

    def test_output_is_non_deterministic(self, key: str) -> None:
        """Fernet embeds a timestamp + IV, so two encryptions differ but both decrypt."""
        cipher = FernetCredentialCipher(key)

        first = cipher.encrypt("same-input")
        second = cipher.encrypt("same-input")

        assert first != second
        assert cipher.decrypt(first) == cipher.decrypt(second) == "same-input"


class TestPassthroughCredentialCipher:
    def test_returns_the_input_unchanged(self) -> None:
        cipher = PassthroughCredentialCipher()

        assert cipher.decrypt("93300116") == "93300116"

    def test_never_raises_on_arbitrary_input(self) -> None:
        cipher = PassthroughCredentialCipher()

        assert cipher.decrypt("!!! anything at all !!!") == "!!! anything at all !!!"

    def test_encrypt_returns_the_input_unchanged(self) -> None:
        cipher = PassthroughCredentialCipher()

        assert cipher.encrypt("93300116") == "93300116"
