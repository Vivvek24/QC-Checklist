"""
E-Signer service schemas (Pydantic v2).
Request/response DTOs for the E-Signer service endpoints.

Additional request/response models will be added as endpoints are implemented.
"""

from typing import Any

from pydantic import BaseModel, Field


class ESignerHealthResponse(BaseModel):
    """Reachability/health of the E-Signer service."""

    service: str
    configured: bool = Field(
        ..., description="Base URL and credentials are all set"
    )
    base_url: str
    status: str
    status_code: int | None = None
    error: str | None = None
    url: str | None = None


# ─── ValidateLogin ───


class ESignerLoginResponseData(BaseModel):
    """The nested ``Response`` object of an E-Signer ValidateLogin call."""

    AuthToken: str = ""
    IsPasswordUpdated: bool = False
    IsPasswordCompliant: bool = False
    ErrorCode: int = 0


class ESignerLoginResponse(BaseModel):
    """
    Result of an E-Signer ValidateLogin call.

    Mirrors the E-Signer wire contract field-for-field. Note that a rejected
    login is returned with ``IsSuccess: false`` (HTTP 200), not an HTTP error.
    """

    IsSuccess: bool = False
    Messages: list[str] = Field(default_factory=list)
    ErrorCode: int = 0
    Response: ESignerLoginResponseData | None = None


# ─── ChangePassword ───


class ESignerChangePasswordResponse(BaseModel):
    """
    Result of a single E-Signer ChangePassword call.

    Mirrors the E-Signer wire contract field-for-field (``Response`` is a bool
    here, unlike ValidateLogin).
    """

    IsSuccess: bool = False
    Messages: list[str] = Field(default_factory=list)
    ErrorCode: int = 0
    Response: bool = False


class ESignerRotatePasswordResponse(BaseModel):
    """
    Result of the two-step password rotation: change to the temporary password,
    then change back to the original. ``IsSuccess`` is true only when both steps
    succeed and the account is restored to the original password.
    """

    IsSuccess: bool = False
    message: str = ""
    step1: ESignerChangePasswordResponse | None = Field(
        default=None, description="Change to the temporary password"
    )
    step2: ESignerChangePasswordResponse | None = Field(
        default=None, description="Restore the original password"
    )


# ─── InitiateEmbeddedSigning ───


class ESignerInitiateSigningResponseData(BaseModel):
    """The nested ``Response`` object of an InitiateEmbeddedSigning call."""

    ReferenceNo: str | None = None
    DocumentNumberList: list[str] | None = None
    DocumentIdList: list[int] | None = None
    Status: bool = False
    WorkflowId: int | None = None
    SignatoryDetails: Any | None = None
    URL: str | None = None
    ParallelSigningURLs: Any | None = None
    TransactionNumber: str | None = None
    RedirectURL: str | None = None
    ResponseCode: str | None = None
    TemplateId: int = 0


class ESignerInitiateSigningResponse(BaseModel):
    """
    Result of an E-Signer InitiateEmbeddedSigning call.

    Mirrors the E-Signer wire contract field-for-field, including the embedded
    signing ``URL`` returned on success.
    """

    IsSuccess: bool = False
    Messages: list[str] = Field(default_factory=list)
    ErrorCode: int = 0
    Response: ESignerInitiateSigningResponseData | None = None


# ─── GetWorkflowInfo ───


class ESignerSignatory(BaseModel):
    """A single signatory entry within a workflow's document details."""

    EmailID: str | None = None
    Name: str | None = None
    Status: str | None = None
    Remarks: str | None = None
    SignerType: int = 0
    SignedDate: str | None = None
    ModeOfSignature: str | None = None
    WorkId: int = 0
    CurrentSignatoryName: str | None = None
    PercentageNameMatch: str | None = None


class ESignerWorkflowInfo(BaseModel):
    """Status/details of a single workflow and its document."""

    Signatories: list[ESignerSignatory] | None = None
    DocumentName: str | None = None
    WorkflowName: str | None = None
    DocumentNumber: str | None = None
    DocumentId: int = 0
    UploadDateTime: str | None = None
    DocumentSize: str | None = None
    NoOfAttachment: int = 0
    NoOfDocuments: int = 0
    SubscriberId: int = 0
    Modifieddate: str | None = None
    DocumentOwner: str | None = None
    ReferenceNo: str | None = None
    CurrentSigner: int = 0
    StatusId: int = 0
    WorkflowType: str | None = None
    LastModifiedBy: str | None = None
    CurrentSignatoryName: str | None = None
    PercentageNameMatch: str | None = None


class ESignerWorkflowInfoResponse(BaseModel):
    """
    Result of an E-Signer GetWorkflowInfo call. ``Response`` is a list of
    workflow/document detail records.
    """

    IsSuccess: bool = False
    Messages: list[str] = Field(default_factory=list)
    ErrorCode: int = 0
    Response: list[ESignerWorkflowInfo] | None = None


# ─── DownloadWorkflowDocuments ───


class ESignerDownloadedFile(BaseModel):
    """A single downloaded document with its base64-encoded content."""

    DocumentName: str | None = None
    Base64FileData: str | None = None
    DocumentId: int = 0
    IsAttachment: bool = False


class ESignerDownloadDocumentsResponseData(BaseModel):
    """The nested ``Response`` object of a DownloadWorkflowDocuments call."""

    ReferenceNo: str | None = None
    WorkflowId: int = 0
    FileList: list[ESignerDownloadedFile] | None = None
    CertificateData: Any | None = None


class ESignerDownloadDocumentsResponse(BaseModel):
    """
    Result of an E-Signer DownloadWorkflowDocuments call. On success the nested
    ``Response.FileList`` contains each document as base64.
    """

    IsSuccess: bool = False
    Messages: list[str] = Field(default_factory=list)
    ErrorCode: int = 0
    Response: ESignerDownloadDocumentsResponseData | None = None


# ─── GetWorkflowAttachments ───


class ESignerWorkflowAttachment(BaseModel):
    """A single attachment of a workflow with its base64-encoded content."""

    DocumentID: int = 0
    AttachmentName: str | None = None
    Base64FileData: str | None = None
    NoOfPages: int = 0
    FileSize: float = 0.0
    Description: str | None = None
    UploadedBy: int = 0
    UploaderName: str | None = None
    UploadedDate: str | None = None


class ESignerWorkflowAttachmentsResponse(BaseModel):
    """
    Result of an E-Signer GetWorkflowAttachments call. ``Response`` is a list of
    attachment records, each carrying its base64-encoded file data.
    """

    IsSuccess: bool = False
    Messages: list[str] = Field(default_factory=list)
    ErrorCode: int = 0
    Response: list[ESignerWorkflowAttachment] | None = None


# ─── GetDocumentLog ───


class ESignerDocumentLogEntry(BaseModel):
    """A single audit-log entry for a document within a workflow."""

    DateTime: str | None = None
    UserEmail: str | None = None
    Action: str | None = None
    IPAddress: str | None = None
    OSandBrowser: str | None = None


class ESignerDocumentLog(BaseModel):
    """The log history for a single document in the workflow."""

    DocumentName: str | None = None
    DocumentLogs: list[ESignerDocumentLogEntry] | None = None


class ESignerDocumentLogResponse(BaseModel):
    """
    Result of an E-Signer GetDocumentLog call. ``Response`` is a list of
    per-document log histories. Note ``Messages`` may be ``null`` here.
    """

    IsSuccess: bool = False
    Messages: list[str] | None = None
    ErrorCode: int = 0
    Response: list[ESignerDocumentLog] | None = None


# ─── GetSigningURL ───


class ESignerSigningUrlResponse(BaseModel):
    """
    Result of an E-Signer GetSigningURL call. ``Response`` is the signing URL
    string when successful.
    """

    IsSuccess: bool = False
    Messages: list[str] = Field(default_factory=list)
    ErrorCode: int = 0
    Response: str | None = None
