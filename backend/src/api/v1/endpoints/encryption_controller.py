"""
Encryption utility API endpoint.

A testing helper that turns a plaintext value into the Fernet token the
published ``/adintegratorservices/rest/v1/validatecredentials`` endpoint
expects. It reuses the same cipher (and therefore the same
``DARWIN_VALIDATE_ENCRYPTION_KEY``) as that endpoint's decrypt side, so a
tester can generate a matching ``EmployeeId`` / ``Password`` token from the UI
instead of running a Python one-liner or hand-editing tokens.

Protected: requires the 'services.encryption' permission. This is deliberately
gated — an open encrypt oracle plus the shared key would let anyone forge
credential tokens.
"""

from fastapi import APIRouter, Depends

from src.api.v1.dependencies import get_credential_cipher
from src.api.v1.schemas.encryption_schema import EncryptRequest, EncryptResponse
from src.domain.services.credential_cipher import ICredentialCipher
from src.infrastructure.security.credential_cipher_impl import FernetCredentialCipher
from src.infrastructure.security.permission_manager import require_permission

router = APIRouter(
    prefix="/services/encryption",
    tags=["Encryption Utility"],
    dependencies=[Depends(require_permission("services.encryption"))],
)


@router.post(
    "/encrypt",
    response_model=EncryptResponse,
    summary="Encrypt a plaintext value into a validatecredentials token",
)
async def encrypt(
    request: EncryptRequest,
    cipher: ICredentialCipher = Depends(get_credential_cipher),
) -> EncryptResponse:
    """
    Encrypt ``plaintext`` with the shared Fernet key and return the token.

    The token is what a consuming app posts as ``EmployeeId`` or ``Password`` to
    the published ``validatecredentials`` endpoint. When
    ``DARWIN_VALIDATE_ENCRYPTION_KEY`` is unset the cipher is a passthrough and
    the plaintext is returned unchanged (``encrypted=false``), matching that
    endpoint's plaintext-accepting mode.
    """
    token = cipher.encrypt(request.plaintext)
    return EncryptResponse(
        token=token,
        encrypted=isinstance(cipher, FernetCredentialCipher),
    )
