/**
 * RBAC Admin feature types.
 * ids are numbers (BigInt from backend).
 */

export interface Permission {
  id: number;
  code: string;
  name: string;
  description: string;
  scope: 'MENU' | 'API' | 'FIELD';
  resource: string;
  action: string;
  is_active: boolean;
  created_date: string;
}

export interface Role {
  id: number;
  code: string;
  name: string;
  description: string;
  is_system: boolean;
  is_active: boolean;
  tenant_id: number | null;
  parent_role_id: number | null;
  permissions: Permission[];
  created_date: string;
  modified_date: string;
}

export interface RoleListResponse {
  roles: Role[];
  total: number;
}

export interface CreateRoleRequest {
  code: string;
  name: string;
  description?: string;
  tenant_id?: number;
  parent_role_id?: number;
}

export interface UpdateRoleRequest {
  name?: string;
  description?: string;
  is_active?: boolean;
  parent_role_id?: number;
}

export interface RoleAssignRequest {
  user_id: number;
  role_id: number;
  tenant_id?: number;
}

export interface PermissionGrantRequest {
  role_id: number;
  permission_id: number;
}

export interface AuditLogEntry {
  id: number;
  actor_id: number | null;
  actor_username: string;
  action: string;
  resource_type: string;
  resource_id: string;
  tenant_id: number | null;
  old_value: string | null;
  new_value: string | null;
  ip_address: string;
  user_agent: string;
  extra_data: string | null;
  created_at: string;
}

export interface AuditLogListResponse {
  logs: AuditLogEntry[];
  total: number;
  skip: number;
  limit: number;
}
