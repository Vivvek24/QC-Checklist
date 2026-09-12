"""
Credential cipher adapters for the published `validatecredentials` endpoint.

Two implementations behind the one `ICredentialCipher` port, selected by whether
`DARWIN_VALIDATE_ENCRYPTION_KEY` is configured (see `get_credential_cipher` in
`dependencies.py`):

- `FernetCredentialCipher` — the real one. Fernet is AES-128-CBC with an HMAC,
  so a tampered or truncated token fails authentication and decryption raises
  rather than returning garbage that might then be tried as an LDAP password.
- `PassthroughCredentialCipher` — returns the input unchanged. Preserves drop-in
  compatibility for callers still sending plaintext, the same opt-in-by-config
  stance the sibling `X-API-Key` check on this endpoint takes.
"""

from cryptography.fernet import Fernet, InvalidToken

from src.domain.services.credential_cipher import (
    CredentialDecryptError,
    ICredentialCipher,
)

__all__ = ["FernetCredentialCipher", "PassthroughCredentialCipher"]


class FernetCredentialCipher(ICredentialCipher):
    """Decrypts credential fields with a shared Fernet key."""

    def __init__(self, key: str) -> None:
        """
        Args:
            key: The urlsafe-base64 32-byte Fernet key, shared with the consuming
                apps. An invalid key raises here, at construction, so a
                misconfigured `DARWIN_VALIDATE_ENCRYPTION_KEY` fails when the
                cipher is built rather than on the first request.
        """
        self._fernet = Fernet(key.encode("utf-8"))

    def encrypt(self, plaintext: str) -> str:
        return self._fernet.encrypt(plaintext.encode("utf-8")).decode("utf-8")

    def decrypt(self, token: str) -> str:
        try:
            return self._fernet.decrypt(token.encode("utf-8")).decode("utf-8")
        except (InvalidToken, ValueError, TypeError) as exc:
            # InvalidToken: not our ciphertext / wrong key / tampered / expired.
            # ValueError, TypeError: not even valid base64. All are "cannot
            # decrypt this"; collapse them so the caller cannot tell which.
            raise CredentialDecryptError("Credential could not be decrypted") from exc


class PassthroughCredentialCipher(ICredentialCipher):
    """Returns the input unchanged — used when no encryption key is configured."""

    def encrypt(self, plaintext: str) -> str:
        return plaintext

    def decrypt(self, token: str) -> str:
        return token
