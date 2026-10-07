/**
 * useUserNameResolver — resolves an acting user's id to a display name on the
 * UI (approval labels store only user_id). No API change; reads the users list.
 */

import { useMemo } from 'react';
import { useUsers } from '../../user-management/hooks/useUsers';

export const useUserNameResolver = (): ((userId: number) => string) => {
  const { data: usersData } = useUsers(0, 500);
  return useMemo(() => {
    const map = new Map<number, string>(
      (usersData?.users ?? []).map((u) => [u.id, u.employee_name || u.username])
    );
    return (userId: number) => map.get(userId) ?? `User #${userId}`;
  }, [usersData]);
};
