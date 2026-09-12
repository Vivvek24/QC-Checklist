/**
 * RBAC Admin API client.
 * Provides CRUD operations for roles, permissions, and audit logs.
 */

import { apiClient } from '@shared/services/apiClient';

import type {
  AuditLogListResponse,
  CreateRoleRequest,
  Permission,
  PermissionGrantRequest,
  Role,
  RoleAssignRequest,
  RoleAssignment,
  RoleListResponse,
  UpdateRoleRequest,
} from '../models/rbac-admin.types';

/**
 * Shape of the grant/revoke endpoints' responses. The backend declares these
 * as a plain `-> dict` with no `response_model`, so there is no richer contract
 * to mirror here; callers currently ignore the body and only care that the
 * request succeeded.
 */
type MutationAck = Record<string, unknown>;

/** Query filters accepted by the audit-log list endpoint. */
export interface AuditLogQueryParams {
  action?: string;
  actor_username?: string;
  resource_type?: string;
  skip?: number;
  limit?: number;
}

const BASE = '/rbac';

export const rbacAdminApi = {
  // ─── Roles ───

  async listRoles(tenantId?: string): Promise<RoleListResponse> {
    const params = tenantId ? { tenant_id: tenantId } : {};
    const response = await apiClient.get<RoleListResponse>(`${BASE}/roles`, { params });
    return response.data;
  },

  async createRole(data: CreateRoleRequest): Promise<Role> {
    const response = await apiClient.post<Role>(`${BASE}/roles`, data);
    return response.data;
  },

  async updateRole(roleId: string, data: UpdateRoleRequest): Promise<Role> {
    const response = await apiClient.patch<Role>(`${BASE}/roles/${roleId}`, data);
    return response.data;
  },

  // ─── Permissions ───

  async listPermissions(scope?: string): Promise<Permission[]> {
    const params = scope ? { scope } : {};
    const response = await apiClient.get<Permission[]>(`${BASE}/permissions`, { params });
    return response.data;
  },

  async grantPermission(data: PermissionGrantRequest): Promise<MutationAck> {
    const response = await apiClient.post<MutationAck>(`${BASE}/roles/grant-permission`, data);
    return response.data;
  },

  async revokePermission(data: PermissionGrantRequest): Promise<MutationAck> {
    const response = await apiClient.post<MutationAck>(`${BASE}/roles/revoke-permission`, data);
    return response.data;
  },

  // ─── Role Assignments ───

  async assignRole(data: RoleAssignRequest): Promise<RoleAssignment> {
    const response = await apiClient.post<RoleAssignment>(`${BASE}/assignments`, data);
    return response.data;
  },

  async revokeRole(data: RoleAssignRequest): Promise<MutationAck> {
    const response = await apiClient.post<MutationAck>(`${BASE}/assignments/revoke`, data);
    return response.data;
  },

  // ─── Audit Logs ───

  async listAuditLogs(params?: AuditLogQueryParams): Promise<AuditLogListResponse> {
    const response = await apiClient.get<AuditLogListResponse>(`${BASE}/audit-logs`, { params });
    return response.data;
  },
};
