/**
 * Encryption Utility API calls.
 * Maps to backend: /api/v1/services/encryption/*
 *
 * Endpoints:
 *   POST /encrypt - Encrypt a plaintext value into a validatecredentials token
 */

import { apiClient } from '@shared/services/apiClient';

export interface EncryptResponse {
  token: string;
  encrypted: boolean;
}

export const encryptionApi = {
  encrypt: async (plaintext: string): Promise<EncryptResponse> => {
    const { data } = await apiClient.post<EncryptResponse>('/services/encryption/encrypt', {
      plaintext,
    });
    return data;
  },
};
