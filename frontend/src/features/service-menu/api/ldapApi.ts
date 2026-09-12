/**
 * LDAP Service API calls.
 * Maps to backend: /api/v1/services/ldap/*
 *
 * Management (CRUD):
 *   GET    /configs            - List LDAP server configurations
 *   POST   /configs            - Create a configuration
 *   GET    /configs/{id}       - Get a configuration
 *   PUT    /configs/{id}       - Update a configuration
 *   DELETE /configs/{id}       - Delete a configuration
 *
 * Services (per-server):
 *   GET  /configs/{id}/health               - Check reachability
 *   POST /configs/{id}/validate-credentials - Validate a user's credentials
 */

import { apiClient } from '@shared/services/apiClient';

export interface LdapConfig {
  id: string;
  name: string;
  server_uri: string;
  base_dn: string;
  bind_username: string;
  domain_prefix: string;
  use_ssl: boolean;
  is_enabled: boolean;
  bind_password_set: boolean;
  created_by: string;
  created_date: string;
  modified_by: string;
  modified_date: string;
}

export interface LdapConfigListResponse {
  configs: LdapConfig[];
  total: number;
}

export interface LdapConfigCreateRequest {
  name: string;
  server_uri: string;
  base_dn: string;
  bind_username: string;
  bind_password: string;
  domain_prefix: string;
  use_ssl: boolean;
  is_enabled: boolean;
}

export interface LdapConfigUpdateRequest {
  name: string;
  server_uri: string;
  base_dn: string;
  bind_username: string;
  bind_password?: string | null;
  domain_prefix: string;
  use_ssl: boolean;
  is_enabled: boolean;
}

export interface LdapHealthResponse {
  id: string;
  name: string;
  configured: boolean;
  server_uri: string;
  status: string;
  error?: string | null;
}

export interface ValidateLdapCredentialsRequest {
  username: string;
  password: string;
}

export interface ValidateLdapCredentialsResponse {
  is_valid: boolean;
  message: string;
  user_dn: string;
  attributes: Record<string, unknown>;
}

export const ldapApi = {
  listConfigs: async (): Promise<LdapConfigListResponse> => {
    const { data } = await apiClient.get<LdapConfigListResponse>('/services/ldap/configs');
    return data;
  },

  createConfig: async (request: LdapConfigCreateRequest): Promise<LdapConfig> => {
    const { data } = await apiClient.post<LdapConfig>('/services/ldap/configs', request);
    return data;
  },

  updateConfig: async (
    id: string,
    request: LdapConfigUpdateRequest
  ): Promise<LdapConfig> => {
    const { data } = await apiClient.put<LdapConfig>(`/services/ldap/configs/${id}`, request);
    return data;
  },

  deleteConfig: async (id: string): Promise<void> => {
    await apiClient.delete(`/services/ldap/configs/${id}`);
  },

  healthCheck: async (id: string): Promise<LdapHealthResponse> => {
    const { data } = await apiClient.get<LdapHealthResponse>(
      `/services/ldap/configs/${id}/health`
    );
    return data;
  },

  validateCredentials: async (
    id: string,
    request: ValidateLdapCredentialsRequest
  ): Promise<ValidateLdapCredentialsResponse> => {
    const { data } = await apiClient.post<ValidateLdapCredentialsResponse>(
      `/services/ldap/configs/${id}/validate-credentials`,
      request
    );
    return data;
  },
};
