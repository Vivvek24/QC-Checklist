/**
 * Published E-Signer Service API calls (drop-in / Catalyst contract).
 *
 * Maps to backend routes mounted at the app root:
 *   POST /rest/embededsign/v1/Login_and_Send_Document  (JSON body -> XML response)
 *   GET  /rest/embededsign/v1/Get_Status?WorkFlowId=<id>
 *   POST /rest/embededsign/v1/Download_Document        (body: { WorkFlowId })
 *   GET  /rest/embededsign/v1/GetAttachments?workflowId=<id>   (bare array)
 *   GET  /rest/embededsign/v1/GetDocumentLogs?workflowId=<id>  (bare array)
 *   GET  /rest/embededsign/v1/GetSignatureURL?WorkflowID=<id>
 *
 * Auth is via the optional `X-API-Key` header (empty = open). Called directly
 * (not through the JWT apiClient) so the harness exercises the exact contract.
 *
 * Note the intentional query-param casing differences per endpoint
 * (WorkFlowId / workflowId / WorkflowID) — these match the legacy service.
 */

import { publishedApiClient, withApiKey } from '@shared/services/publishedApiClient';

const BASE = '/rest/embededsign/v1';

export interface EsignerEnvelope<T> {
  IsSuccess: boolean;
  Messages: string[] | null;
  ErrorCode: number;
  Response: T;
}

export interface PublishedAttachment {
  AttachmentName: string | null;
  Base64FileData: string | null;
  UploadedBy: number;
  UploaderName: string | null;
}

export interface PublishedDocumentLog {
  DateTime: string | null;
  UserEmail: string | null;
  Action: string | null;
  IPAddress: string | null;
}

export const publishedEsignerApi = {
  loginAndSendDocument: async (
    apiKey: string,
    body: Record<string, unknown>
  ): Promise<string> => {
    const { data } = await publishedApiClient.post<string>(
      `${BASE}/Login_and_Send_Document`,
      body,
      withApiKey(apiKey, {
        headers: { 'Content-Type': 'application/json', Accept: 'application/xml' },
        responseType: 'text',
      })
    );
    return data;
  },

  getStatus: async (apiKey: string, workFlowId: number): Promise<unknown> => {
    const { data } = await publishedApiClient.get(
      `${BASE}/Get_Status`,
      withApiKey(apiKey, { params: { WorkFlowId: workFlowId } })
    );
    return data;
  },

  downloadDocument: async (apiKey: string, workFlowId: number): Promise<unknown> => {
    const { data } = await publishedApiClient.post(
      `${BASE}/Download_Document`,
      { WorkFlowId: workFlowId },
      withApiKey(apiKey, {
        headers: { 'Content-Type': 'application/json' },
      })
    );
    return data;
  },

  getAttachments: async (
    apiKey: string,
    workflowId: number
  ): Promise<PublishedAttachment[]> => {
    const { data } = await publishedApiClient.get<PublishedAttachment[]>(
      `${BASE}/GetAttachments`,
      withApiKey(apiKey, { params: { workflowId } })
    );
    return data;
  },

  getDocumentLogs: async (
    apiKey: string,
    workflowId: number
  ): Promise<PublishedDocumentLog[]> => {
    const { data } = await publishedApiClient.get<PublishedDocumentLog[]>(
      `${BASE}/GetDocumentLogs`,
      withApiKey(apiKey, { params: { workflowId } })
    );
    return data;
  },

  getSignatureUrl: async (apiKey: string, workflowId: number): Promise<unknown> => {
    const { data } = await publishedApiClient.get(
      `${BASE}/GetSignatureURL`,
      withApiKey(apiKey, { params: { WorkflowID: workflowId } })
    );
    return data;
  },
};
