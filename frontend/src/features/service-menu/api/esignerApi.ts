/**
 * E-Signer Service API calls.
 * Maps to backend: /api/v1/services/esigner/*
 *
 * Endpoints:
 *   GET /health - Service reachability + configured flag
 *
 * Additional endpoints will be added one by one as they are implemented.
 */

import { apiClient } from '@shared/services/apiClient';

export interface EsignerHealthResponse {
  service: string;
  configured: boolean;
  base_url: string;
  status: string;
  status_code?: number;
  url?: string;
  error?: string;
}

export interface EsignerLoginResponseData {
  AuthToken: string;
  IsPasswordUpdated: boolean;
  IsPasswordCompliant: boolean;
  ErrorCode: number;
}

export interface EsignerLoginResponse {
  IsSuccess: boolean;
  Messages: string[];
  ErrorCode: number;
  Response: EsignerLoginResponseData | null;
}

export interface EsignerChangePasswordResponse {
  IsSuccess: boolean;
  Messages: string[];
  ErrorCode: number;
  Response: boolean;
}

export interface EsignerRotatePasswordResponse {
  IsSuccess: boolean;
  message: string;
  step1: EsignerChangePasswordResponse | null;
  step2: EsignerChangePasswordResponse | null;
}

export interface EsignerInitiateSigningResponseData {
  ReferenceNo: string | null;
  DocumentNumberList: string[] | null;
  DocumentIdList: number[] | null;
  Status: boolean;
  WorkflowId: number | null;
  SignatoryDetails: unknown | null;
  URL: string | null;
  ParallelSigningURLs: unknown | null;
  TransactionNumber: string | null;
  RedirectURL: string | null;
  ResponseCode: string | null;
  TemplateId: number;
}

export interface EsignerInitiateSigningResponse {
  IsSuccess: boolean;
  Messages: string[];
  ErrorCode: number;
  Response: EsignerInitiateSigningResponseData | null;
}

export interface EsignerSignatory {
  EmailID: string | null;
  Name: string | null;
  Status: string | null;
  Remarks: string | null;
  SignerType: number;
  SignedDate: string | null;
  ModeOfSignature: string | null;
  WorkId: number;
  CurrentSignatoryName: string | null;
  PercentageNameMatch: string | null;
}

export interface EsignerWorkflowInfo {
  Signatories: EsignerSignatory[] | null;
  DocumentName: string | null;
  WorkflowName: string | null;
  DocumentNumber: string | null;
  DocumentId: number;
  UploadDateTime: string | null;
  DocumentSize: string | null;
  NoOfAttachment: number;
  NoOfDocuments: number;
  SubscriberId: number;
  Modifieddate: string | null;
  DocumentOwner: string | null;
  ReferenceNo: string | null;
  CurrentSigner: number;
  StatusId: number;
  WorkflowType: string | null;
  LastModifiedBy: string | null;
  CurrentSignatoryName: string | null;
  PercentageNameMatch: string | null;
}

export interface EsignerWorkflowInfoResponse {
  IsSuccess: boolean;
  Messages: string[];
  ErrorCode: number;
  Response: EsignerWorkflowInfo[] | null;
}

export interface EsignerDownloadedFile {
  DocumentName: string | null;
  Base64FileData: string | null;
  DocumentId: number;
  IsAttachment: boolean;
}

export interface EsignerDownloadDocumentsResponseData {
  ReferenceNo: string | null;
  WorkflowId: number;
  FileList: EsignerDownloadedFile[] | null;
  CertificateData: unknown | null;
}

export interface EsignerDownloadDocumentsResponse {
  IsSuccess: boolean;
  Messages: string[];
  ErrorCode: number;
  Response: EsignerDownloadDocumentsResponseData | null;
}

export interface EsignerWorkflowAttachment {
  DocumentID: number;
  AttachmentName: string | null;
  Base64FileData: string | null;
  NoOfPages: number;
  FileSize: number;
  Description: string | null;
  UploadedBy: number;
  UploaderName: string | null;
  UploadedDate: string | null;
}

export interface EsignerWorkflowAttachmentsResponse {
  IsSuccess: boolean;
  Messages: string[];
  ErrorCode: number;
  Response: EsignerWorkflowAttachment[] | null;
}

export interface EsignerDocumentLogEntry {
  DateTime: string | null;
  UserEmail: string | null;
  Action: string | null;
  IPAddress: string | null;
  OSandBrowser: string | null;
}

export interface EsignerDocumentLog {
  DocumentName: string | null;
  DocumentLogs: EsignerDocumentLogEntry[] | null;
}

export interface EsignerDocumentLogResponse {
  IsSuccess: boolean;
  Messages: string[] | null;
  ErrorCode: number;
  Response: EsignerDocumentLog[] | null;
}

export interface EsignerSigningUrlResponse {
  IsSuccess: boolean;
  Messages: string[];
  ErrorCode: number;
  Response: string | null;
}

export const esignerApi = {
  healthCheck: async (): Promise<EsignerHealthResponse> => {
    const { data } = await apiClient.get<EsignerHealthResponse>(
      '/services/esigner/health'
    );
    return data;
  },

  login: async (): Promise<EsignerLoginResponse> => {
    const { data } = await apiClient.post<EsignerLoginResponse>(
      '/services/esigner/login'
    );
    return data;
  },

  changePassword: async (): Promise<EsignerRotatePasswordResponse> => {
    const { data } = await apiClient.post<EsignerRotatePasswordResponse>(
      '/services/esigner/change-password'
    );
    return data;
  },

  initiateEmbeddedSigning: async (
    payload: Record<string, unknown>
  ): Promise<EsignerInitiateSigningResponse> => {
    const { data } = await apiClient.post<EsignerInitiateSigningResponse>(
      '/services/esigner/initiate-embedded-signing',
      payload
    );
    return data;
  },

  getWorkflowInfo: async (
    workflowId: number
  ): Promise<EsignerWorkflowInfoResponse> => {
    const { data } = await apiClient.get<EsignerWorkflowInfoResponse>(
      '/services/esigner/workflow-info',
      { params: { workflow_id: workflowId } }
    );
    return data;
  },

  downloadWorkflowDocuments: async (
    workflowId: number
  ): Promise<EsignerDownloadDocumentsResponse> => {
    const { data } = await apiClient.get<EsignerDownloadDocumentsResponse>(
      '/services/esigner/workflow-documents',
      { params: { workflow_id: workflowId } }
    );
    return data;
  },

  getWorkflowAttachments: async (
    workflowId: number
  ): Promise<EsignerWorkflowAttachmentsResponse> => {
    const { data } = await apiClient.get<EsignerWorkflowAttachmentsResponse>(
      '/services/esigner/workflow-attachments',
      { params: { workflow_id: workflowId } }
    );
    return data;
  },

  getDocumentLog: async (
    workflowId: number
  ): Promise<EsignerDocumentLogResponse> => {
    const { data } = await apiClient.get<EsignerDocumentLogResponse>(
      '/services/esigner/document-log',
      { params: { workflow_id: workflowId } }
    );
    return data;
  },

  getSigningUrl: async (
    workflowId: number
  ): Promise<EsignerSigningUrlResponse> => {
    const { data } = await apiClient.get<EsignerSigningUrlResponse>(
      '/services/esigner/signing-url',
      { params: { workflow_id: workflowId } }
    );
    return data;
  },
};
