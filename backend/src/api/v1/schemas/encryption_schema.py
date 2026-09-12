"""
Encryption utility schemas (Pydantic v2).

Request/response DTOs for the testing helper that encrypts a plaintext value
into the Fernet token the published ``validatecredentials`` endpoint expects.
"""

from pydantic import BaseModel, Field


class EncryptRequest(BaseModel):
    """A single plaintext value to encrypt."""

    plaintext: str = Field(
        ...,
        min_length=1,
        description="The plaintext value (e.g. an employee id or password) to encrypt.",
    )


class EncryptResponse(BaseModel):
    """The encrypted token for a plaintext value."""

    token: str = Field(
        ...,
        description=(
            "The encrypted token. Post this as the EmployeeId or Password form "
            "field to /adintegratorservices/rest/v1/validatecredentials. When no "
            "encryption key is configured the value is returned unchanged."
        ),
    )
    encrypted: bool = Field(
        ...,
        description=(
            "True when a real Fernet key is configured and the token is "
            "encrypted; False when the service is in passthrough (plaintext) mode."
        ),
    )
