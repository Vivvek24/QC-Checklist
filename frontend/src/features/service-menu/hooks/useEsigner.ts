/**
 * TanStack Query hooks for E-Signer Service operations.
 */

import { useMutation, useQuery } from '@tanstack/react-query';

import { esignerApi } from '../api/esignerApi';

export const useEsignerHealth = () => {
  return useQuery({
    queryKey: ['esigner', 'health'],
    queryFn: () => esignerApi.healthCheck(),
    staleTime: 10_000,
    retry: 1,
  });
};

export const useEsignerLogin = () => {
  return useMutation({
    mutationFn: () => esignerApi.login(),
  });
};

export const useEsignerChangePassword = () => {
  return useMutation({
    mutationFn: () => esignerApi.changePassword(),
  });
};

export const useEsignerInitiateSigning = () => {
  return useMutation({
    mutationFn: (payload: Record<string, unknown>) => esignerApi.initiateEmbeddedSigning(payload),
  });
};

export const useEsignerWorkflowInfo = () => {
  return useMutation({
    mutationFn: (workflowId: number) => esignerApi.getWorkflowInfo(workflowId),
  });
};

export const useEsignerWorkflowDocuments = () => {
  return useMutation({
    mutationFn: (workflowId: number) => esignerApi.downloadWorkflowDocuments(workflowId),
  });
};

export const useEsignerWorkflowAttachments = () => {
  return useMutation({
    mutationFn: (workflowId: number) => esignerApi.getWorkflowAttachments(workflowId),
  });
};

export const useEsignerDocumentLog = () => {
  return useMutation({
    mutationFn: (workflowId: number) => esignerApi.getDocumentLog(workflowId),
  });
};

export const useEsignerSigningUrl = () => {
  return useMutation({
    mutationFn: (workflowId: number) => esignerApi.getSigningUrl(workflowId),
  });
};
