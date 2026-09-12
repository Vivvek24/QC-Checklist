/**
 * TanStack Query hooks for LDAP Service operations.
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

import {
  ldapApi,
  type LdapConfigCreateRequest,
  type LdapConfigUpdateRequest,
  type ValidateLdapCredentialsRequest,
} from '../api/ldapApi';

export const useLdapConfigs = () => {
  return useQuery({
    queryKey: ['ldap', 'configs'],
    queryFn: () => ldapApi.listConfigs(),
    staleTime: 30_000,
  });
};

export const useCreateLdapConfig = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (request: LdapConfigCreateRequest) => ldapApi.createConfig(request),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['ldap', 'configs'] });
    },
  });
};

export const useUpdateLdapConfig = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, request }: { id: string; request: LdapConfigUpdateRequest }) =>
      ldapApi.updateConfig(id, request),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['ldap', 'configs'] });
    },
  });
};

export const useDeleteLdapConfig = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => ldapApi.deleteConfig(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['ldap', 'configs'] });
    },
  });
};

export const useLdapHealth = (id: string, enabled = true) => {
  return useQuery({
    queryKey: ['ldap', 'health', id],
    queryFn: () => ldapApi.healthCheck(id),
    enabled: enabled && !!id,
    staleTime: 10_000,
    retry: 1,
  });
};

export const useValidateLdapCredentials = () => {
  return useMutation({
    mutationFn: ({ id, request }: { id: string; request: ValidateLdapCredentialsRequest }) =>
      ldapApi.validateCredentials(id, request),
  });
};
