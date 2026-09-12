"""
Credential cipher port.

The published `validatecredentials` endpoint receives a username and password that
a consuming application encrypted with a shared key. Decryption is an infrastructure
concern (the algorithm and key handling live in the adapter), but the controller needs
to turn a ciphertext back into plaintext before the LDAP bind — so it depends on this
interface, keeping that dependency pointing inwards.
"""

from abc import ABC, abstractmethod


class CredentialDecryptError(Exception):
    """
    A supplied credential token could not be decrypted.

    Raised for a malformed, tampered, wrong-key, or truncated token. Carries no
    detail about which of those it was: the caller turns this into a generic
    validation failure, and leaking the distinction would help an attacker probe
    the key.
    """


class ICredentialCipher(ABC):
    """Turns an encrypted credential field back into plaintext for the LDAP bind."""

    @abstractmethod
    def encrypt(self, plaintext: str) -> str:
        """
        Return an encrypted token for a plaintext credential field.

        The inverse of :meth:`decrypt`, exposed so a testing helper can produce
        the tokens a consuming app would send to ``validatecredentials`` without
        that app having to reimplement the encryption. When no key is configured
        the passthrough cipher returns the input unchanged, matching the
        plaintext-accepting stance of the decrypt side.
        """
        ...

    @abstractmethod
    def decrypt(self, token: str) -> str:
        """
        Return the plaintext for an encrypted credential field.

        Raises:
            CredentialDecryptError: The token is not something this cipher produced
                with its configured key.
        """
        ...
