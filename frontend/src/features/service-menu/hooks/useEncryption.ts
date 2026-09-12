/**
 * TanStack Query hooks for the Encryption Utility.
 */

import { useMutation } from '@tanstack/react-query';

import { encryptionApi } from '../api/encryptionApi';

export const useEncrypt = () => {
  return useMutation({
    mutationFn: (plaintext: string) => encryptionApi.encrypt(plaintext),
  });
};
