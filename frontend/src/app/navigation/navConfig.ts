/**
 * Central navigation config — the single source of truth for the sidebar and
 * the dashboard tiles. Keeping one list ensures both stay in sync (labels,
 * icons, routes, RBAC menu keys, and section order).
 */

export interface NavItem {
  label: string;
  icon: string;
  path: string;
  /** When false, hide even without an RBAC menuKey (static items). */
  visible?: boolean;
  /** Sidebar/dashboard grouping. Sections render in first-seen order. */
  section?: string;
  /** RBAC menu key required to see this item. Omit for always-visible items. */
  menuKey?: string;
  /** Optional one-line description shown on the dashboard tile. */
  description?: string;
}

/**
 * Ordered navigation items. Section order in the UI follows the order these
 * first appear here (Main → Services → Published Services → Management).
 * The Dashboard itself is intentionally excluded (it's the landing page).
 */
export const NAV_ITEMS: NavItem[] = [
  {
    label: 'Dashboard',
    icon: 'pi pi-th-large',
    path: '/dashboard',
    section: 'Main',
    menuKey: 'dashboard',
  },
  {
    label: 'Employees',
    icon: 'pi pi-id-card',
    path: '/employees',
    section: 'Main',
    menuKey: 'employees',
    description: 'Browse the employee directory',
  },
  {
    label: 'LDAP Servers',
    icon: 'pi pi-server',
    path: '/ldap-servers',
    section: 'Main',
    menuKey: 'ldap',
    description: 'Manage LDAP/AD server configuration',
  },
  {
    label: 'Employee AD',
    icon: 'pi pi-id-card',
    path: '/services/employee-ad',
    section: 'Services',
    menuKey: 'services',
    description: 'Verify the Darwin AD integration',
  },
  {
    label: 'Darwinbox',
    icon: 'pi pi-users',
    path: '/services/darwinbox',
    section: 'Services',
    menuKey: 'services',
    description: 'Sync and preview Darwinbox data',
  },
  {
    label: 'LDAP',
    icon: 'pi pi-sitemap',
    path: '/services/ldap',
    section: 'Services',
    menuKey: 'services',
    description: 'Test LDAP servers and credentials',
  },
  {
    label: 'E-Signer',
    icon: 'pi pi-pencil',
    path: '/services/esigner',
    section: 'Services',
    menuKey: 'services',
    description: 'Test the E-Signer integration',
  },
  {
    label: 'Encryption',
    icon: 'pi pi-lock',
    path: '/services/encryption',
    section: 'Services',
    menuKey: 'services',
    description: 'Encrypt a value for validatecredentials',
  },
  {
    label: 'Darwin AD',
    icon: 'pi pi-globe',
    path: '/published-services/darwin-ad',
    section: 'Published Services',
    menuKey: 'published_services',
    description: 'Drop-in Darwin AD endpoints for other apps',
  },
  {
    label: 'E-Signer',
    icon: 'pi pi-pencil',
    path: '/published-services/esigner',
    section: 'Published Services',
    menuKey: 'published_services',
    description: 'Drop-in E-Signer endpoints for other apps',
  },
  {
    label: 'Users',
    icon: 'pi pi-users',
    path: '/users',
    section: 'Management',
    menuKey: 'users',
    description: 'Manage application users',
  },
  {
    label: 'Roles & Permissions',
    icon: 'pi pi-shield',
    path: '/roles',
    section: 'Management',
    menuKey: 'roles',
    description: 'Configure roles and RBAC permissions',
  },
  {
    label: 'Audit Logs',
    icon: 'pi pi-history',
    path: '/audit-logs',
    section: 'Management',
    menuKey: 'audit_logs',
    description: 'Review system audit history',
  },
];

/**
 * Filter nav items by the user's RBAC menu keys.
 * Items without a menuKey follow their `visible` flag (default visible).
 */
export const filterNavItemsByRbac = (
  items: NavItem[],
  menuKeys: string[],
  rbacLoaded: boolean,
): NavItem[] =>
  items.filter((item) => {
    if (!item.menuKey) return item.visible !== false;
    if (!rbacLoaded) return false;
    return menuKeys.includes(item.menuKey);
  });

/** Group items by section, preserving first-seen section order. */
export const groupNavItemsBySection = (items: NavItem[]): Record<string, NavItem[]> =>
  items.reduce<Record<string, NavItem[]>>((acc, item) => {
    const section = item.section || 'Other';
    if (!acc[section]) acc[section] = [];
    acc[section].push(item);
    return acc;
  }, {});
