/**
 * Hook to fetch roles from the RBAC roles table.
 * Returns role ID as number for use with role_assignments.
 */

import { useEffect, useState } from 'react';
import { apiClient } from '@shared/services/apiClient';

interface RoleOption {
  label: string;
  value: number; // role ID (BigInt)
}

interface RoleFromApi {
  id: number;
  code: string;
  name: string;
  is_active: boolean;
}

interface RoleListResponse {
  roles: RoleFromApi[];
  total: number;
}

export const useRoles = () => {
  const [roleOptions, setRoleOptions] = useState<RoleOption[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchRoles = async () => {
      try {
        const response = await apiClient.get<RoleListResponse>('/rbac/roles');
        const options = response.data.roles
          .filter((r) => r.is_active)
          .map((r) => ({
            label: `${r.name} (${r.code})`,
            value: r.id,
          }));
        setRoleOptions(options);
      } catch {
        setRoleOptions([]);
      } finally {
        setLoading(false);
      }
    };

    fetchRoles();
  }, []);

  return { roleOptions, loading };
};
