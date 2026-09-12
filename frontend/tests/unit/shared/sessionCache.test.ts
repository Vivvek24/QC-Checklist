import { afterEach, describe, expect, it } from 'vitest';

import { sessionCache } from '@shared/services/sessionCache';

/**
 * Note this service exposes only the user + menu/permission snapshot. There is
 * no `setApiRbac`/`getApiCodes` here, because this app has no
 * `rbac/my-permissions/api` endpoint — API authorisation is enforced
 * server-side by `require_permission()`.
 */
describe('sessionCache', () => {
  afterEach(() => {
    sessionStorage.clear();
  });

  it('returns empty defaults when nothing has been cached yet', () => {
    expect(sessionCache.getUser()).toBeNull();
    expect(sessionCache.getMenuKeys()).toEqual([]);
    expect(sessionCache.getPermissions()).toEqual([]);
    expect(sessionCache.hasUser()).toBe(false);
  });

  it('stores and retrieves the current user', () => {
    const user = { id: '1', username: 'alice', is_active: true };

    sessionCache.setUser(user);

    expect(sessionCache.getUser()).toEqual(user);
    expect(sessionCache.hasUser()).toBe(true);
  });

  it('stores menu keys and permissions together via setRbac', () => {
    sessionCache.setRbac(
      ['dashboard', 'employees'],
      [
        {
          id: 'p1',
          code: 'menu.employees',
          name: 'Employees Menu',
          description: '',
          scope: 'MENU',
          resource: 'employees',
          action: 'READ',
          is_active: true,
        },
      ],
    );

    expect(sessionCache.getMenuKeys()).toEqual(['dashboard', 'employees']);
    expect(sessionCache.getPermissions()).toHaveLength(1);
  });

  it('merges writes rather than clobbering unrelated keys', () => {
    sessionCache.setUser({ id: '1', username: 'alice', is_active: true });
    sessionCache.setRbac(['dashboard'], []);

    // Setting RBAC data should not have wiped the user that was set earlier.
    expect(sessionCache.getUser()).not.toBeNull();
    expect(sessionCache.getMenuKeys()).toEqual(['dashboard']);
  });

  it('clears everything back to defaults', () => {
    sessionCache.setUser({ id: '1', username: 'alice', is_active: true });
    sessionCache.setRbac(['dashboard'], []);

    sessionCache.clear();

    expect(sessionCache.hasUser()).toBe(false);
    expect(sessionCache.getMenuKeys()).toEqual([]);
  });

  it('recovers to defaults instead of throwing when the stored value is malformed JSON', () => {
    sessionStorage.setItem('session_snapshot_v1', '{not valid json');

    expect(sessionCache.getUser()).toBeNull();
    expect(sessionCache.getMenuKeys()).toEqual([]);
  });
});
