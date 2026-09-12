/**
 * TanStack Query hooks for the Published E-Signer Service test harness.
 *
 * Each hook is a mutation so calls are triggered explicitly from the UI. The
 * `apiKey` is threaded through from the page-level input.
 */

import { useMutation } from '@tanstack/react-query';

import { publishedEsignerApi } from '../api/publishedEsignerApi';

export const usePublishedLoginAndSend = () => {
  return useMutation({
    mutationFn: (vars: { apiKey: string; body: Record<string, unknown> }) =>
      publishedEsignerApi.loginAndSendDocument(vars.apiKey, vars.body),
  });
};

export const usePublishedGetStatus = () => {
  return useMutation({
    mutationFn: (vars: { apiKey: string; workFlowId: number }) =>
      publishedEsignerApi.getStatus(vars.apiKey, vars.workFlowId),
  });
};

export const usePublishedDownloadDocument = () => {
  return useMutation({
    mutationFn: (vars: { apiKey: string; workFlowId: number }) =>
      publishedEsignerApi.downloadDocument(vars.apiKey, vars.workFlowId),
  });
};

export const usePublishedGetAttachments = () => {
  return useMutation({
    mutationFn: (vars: { apiKey: string; workflowId: number }) =>
      publishedEsignerApi.getAttachments(vars.apiKey, vars.workflowId),
  });
};

export const usePublishedGetDocumentLogs = () => {
  return useMutation({
    mutationFn: (vars: { apiKey: string; workflowId: number }) =>
      publishedEsignerApi.getDocumentLogs(vars.apiKey, vars.workflowId),
  });
};

export const usePublishedGetSignatureUrl = () => {
  return useMutation({
    mutationFn: (vars: { apiKey: string; workflowId: number }) =>
      publishedEsignerApi.getSignatureUrl(vars.apiKey, vars.workflowId),
  });
};
