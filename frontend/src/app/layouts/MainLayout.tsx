/**
 * Main application layout — collapsible sidebar sections with QC-Checklist branding.
 */

import { useState, useRef } from 'react';
import { Outlet, useNavigate, useLocation } from 'react-router-dom';
import { Button } from 'primereact/button';
import { Avatar } from 'primereact/avatar';
import { Menu } from 'primereact/menu';
import { Badge } from 'primereact/badge';
import { Tooltip } from 'primereact/tooltip';
import { useAppDispatch, useAppSelector } from '@app/store';
import { logoutThunk } from '@features/authentication/store/authSlice';
import { useApiPermissions, useMenuPermissions } from '@core/rbac/usePermissions';

interface NavItem {
  label: string;
  icon: string;
  path: string;
  section?: string;
  menuKey?: string | string[];
}

interface SectionDef {
  key: string;
  label: string;
  icon: string;
}

const SECTIONS: SectionDef[] = [
  { key: 'Management', label: 'Admin Settings', icon: 'pi pi-cog' },
  { key: 'Masters', label: 'Masters', icon: 'pi pi-database' },
  { key: 'Workflow', label: 'Workflow', icon: 'pi pi-share-alt' },
  { key: 'Services', label: 'Services', icon: 'pi pi-cloud' },
];

export const MainLayout = () => {
  const dispatch = useAppDispatch();
  const navigate = useNavigate();
  const location = useLocation();
  const { user } = useAppSelector((state) => state.auth);
  const userMenu = useRef<Menu>(null);
  const { menuKeys, isLoaded: rbacLoaded } = useMenuPermissions();
  useApiPermissions();
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [expandedSections, setExpandedSections] = useState<Record<string, boolean>>(() => {
    const path = window.location.pathname;
    const result: Record<string, boolean> = {};
    if (path.startsWith('/masters')) result['Masters'] = true;
    else if (path.startsWith('/users') || path.startsWith('/roles') || path.startsWith('/audit')) result['Management'] = true;
    else if (path.startsWith('/workflows') || path.startsWith('/approval')) result['Workflow'] = true;
    else if (path.startsWith('/services')) result['Services'] = true;
    else result['Main'] = true;
    return result;
  });

  const navItems: NavItem[] = [
    { label: 'Dashboard', icon: 'pi pi-th-large', path: '/dashboard', menuKey: 'dashboard' },
    { label: 'Users', icon: 'pi pi-users', path: '/users', section: 'Management', menuKey: 'users' },
    { label: 'Roles & Permissions', icon: 'pi pi-shield', path: '/roles', section: 'Management', menuKey: 'roles' },
    { label: 'Audit Logs', icon: 'pi pi-history', path: '/audit-logs', section: 'Management', menuKey: 'audit_logs' },
    { label: 'Business Units', icon: 'pi pi-building', path: '/masters/business-units', section: 'Masters', menuKey: ['masters', 'masters.business_units'] },
    { label: 'Units', icon: 'pi pi-box', path: '/masters/units', section: 'Masters', menuKey: ['masters', 'masters.units'] },
    { label: 'Formats', icon: 'pi pi-file-edit', path: '/masters/formats', section: 'Masters', menuKey: ['masters', 'masters.formats'] },
    { label: 'Stages', icon: 'pi pi-list', path: '/masters/stages', section: 'Masters', menuKey: ['masters', 'masters.stages'] },
    { label: 'Questions', icon: 'pi pi-question-circle', path: '/masters/questions', section: 'Masters', menuKey: ['masters', 'masters.questions'] },
    { label: 'Products', icon: 'pi pi-shopping-bag', path: '/masters/products', section: 'Masters', menuKey: ['masters', 'masters.products'] },
    { label: 'Validation Types', icon: 'pi pi-check-circle', path: '/masters/validation-types', section: 'Masters', menuKey: ['masters', 'masters.validation_types'] },
    { label: 'Remarks', icon: 'pi pi-comment', path: '/masters/remarks', section: 'Masters', menuKey: ['masters', 'masters.remarks'] },
    { label: 'SAP Fields', icon: 'pi pi-database', path: '/masters/sap-fields', section: 'Masters', menuKey: ['masters', 'masters.sap_fields'] },
    { label: 'Stage Question Mapping', icon: 'pi pi-map', path: '/masters/formats-view', section: 'Masters', menuKey: ['masters', 'masters.stage_question_mapping'] },
    { label: 'Workflows', icon: 'pi pi-share-alt', path: '/workflows', section: 'Workflow', menuKey: 'workflows' },
    { label: 'Approval Matrix', icon: 'pi pi-sliders-h', path: '/approval-matrix', section: 'Workflow', menuKey: 'workflows' },
    { label: 'Employee AD', icon: 'pi pi-id-card', path: '/services/employee-ad', section: 'Services', menuKey: 'services' },
  ];

  const visibleItems = navItems.filter((item) => {
    if (!item.menuKey) return true;
    if (!rbacLoaded) return false;
    const required = Array.isArray(item.menuKey) ? item.menuKey : [item.menuKey];
    return required.every((key) => menuKeys.includes(key));
  });

  const sections = visibleItems.reduce<Record<string, NavItem[]>>((acc, item) => {
    const section = item.section || 'Other';
    if (!acc[section]) acc[section] = [];
    acc[section].push(item);
    return acc;
  }, {});

  const toggleSection = (key: string) => {
    setExpandedSections((prev) => ({ ...prev, [key]: !prev[key] }));
  };

  const userMenuItems = [
    { label: `${user?.username}`, icon: 'pi pi-user', disabled: true },
    { separator: true },
    { label: 'Profile', icon: 'pi pi-id-card', command: () => navigate('/profile') },
    { label: 'Logout', icon: 'pi pi-sign-out', command: async () => { await dispatch(logoutThunk()); navigate('/login', { replace: true }); } },
  ];

  const currentPage = navItems.find((i) => i.path === location.pathname)?.label || '';
  const sidebarWidth = sidebarCollapsed ? '60px' : '230px';

  return (
    <div className="flex" style={{ height: '100vh', background: 'var(--color-surface-ground)', overflow: 'hidden' }}>
      {/* ─── Sidebar ─── */}
      <aside
        className="em-sidebar flex-shrink-0 flex flex-column transition-all transition-duration-200"
        style={{ width: sidebarWidth, height: '100vh', overflow: 'hidden' }}
        aria-label="Sidebar navigation"
      >
        {/* Logo area */}
        <div className={`em-logo-area flex align-items-center ${sidebarCollapsed ? 'justify-content-center' : 'justify-content-between'} px-3`}>
          <span className="flex align-items-center gap-2 cursor-pointer"
            onClick={() => { if (sidebarCollapsed) setSidebarCollapsed(false); }}>
            <span className="em-app-icon flex align-items-center justify-content-center flex-shrink-0">
              <i className="pi pi-book" />
            </span>
            {!sidebarCollapsed && (
              <span className="em-app-name font-bold">QC-Checklist</span>
            )}
          </span>
          {!sidebarCollapsed && (
            <span className="em-collapse-btn flex align-items-center justify-content-center cursor-pointer"
              onClick={() => setSidebarCollapsed(true)}>
              <i className="pi pi-angle-double-left" />
            </span>
          )}
        </div>

        {/* Navigation with collapsible sections */}
        <nav className="flex-1 overflow-y-auto py-2 px-2">
          {/* Dashboard — standalone top-level item */}
          {visibleItems.filter((i) => !i.section).map((item) => {
            const isActive = location.pathname === item.path;
            return sidebarCollapsed ? (
              <div key={item.path} className="flex justify-content-center py-2 cursor-pointer"
                style={{ marginBottom: '0.4rem' }}
                onClick={() => navigate(item.path)}
                data-pr-tooltip={item.label} data-pr-position="right">
                <i className={item.icon} style={{ fontSize: '1.1rem', color: isActive ? 'var(--color-primary)' : 'var(--color-text-muted)' }} />
              </div>
            ) : (
              <button
                key={item.path}
                onClick={() => navigate(item.path)}
                className={`em-nav-section w-full flex align-items-center gap-2 border-none cursor-pointer transition-colors transition-duration-200 py-2 ${isActive ? 'em-nav-active' : ''}`}
                aria-label={item.label}
                aria-current={isActive ? 'page' : undefined}
              >
                <i className={item.icon} />
                <span>{item.label}</span>
              </button>
            );
          })}

          {SECTIONS.map((sectionDef) => {
            const items = sections[sectionDef.key];
            if (!items || items.length === 0) return null;
            const isExpanded = expandedSections[sectionDef.key] ?? false;
            const hasActiveChild = items.some((i) => location.pathname === i.path);

            return (
              <div key={sectionDef.key} className="mb-1">
                {/* Section header — collapsible */}
                {!sidebarCollapsed ? (
                  <button
                    onClick={() => toggleSection(sectionDef.key)}
                    className="em-nav-section w-full flex align-items-center justify-content-between border-none cursor-pointer py-2"
                    aria-expanded={isExpanded}
                    aria-label={`${sectionDef.label} section`}
                  >
                    <span className="flex align-items-center gap-2">
                      <i className={sectionDef.icon} />
                      <span>{sectionDef.label}</span>
                    </span>
                    <i className={`em-nav-chevron ${isExpanded ? 'pi pi-chevron-down' : 'pi pi-chevron-right'}`} />
                  </button>
                ) : (
                  <div className="flex justify-content-center py-2"
                    style={{ marginBottom: '0.4rem' }}
                    data-pr-tooltip={sectionDef.label} data-pr-position="right">
                    <i className={sectionDef.icon} style={{ fontSize: '1.1rem', color: hasActiveChild ? 'var(--color-primary)' : 'var(--color-text-muted)' }} />
                  </div>
                )}

                {/* Section children — visible only when expanded AND sidebar is not collapsed */}
                {isExpanded && !sidebarCollapsed && items.map((item) => {
                  const isActive = location.pathname === item.path;
                  return (
                    <button
                      key={item.path}
                      onClick={() => navigate(item.path)}
                      className={`em-nav-item w-full flex align-items-center gap-2 border-none cursor-pointer transition-colors transition-duration-200 pr-2 py-2 ${isActive ? 'em-nav-active' : ''}`}
                      aria-label={item.label}
                      aria-current={isActive ? 'page' : undefined}
                    >
                      <i className={item.icon} />
                      <span>{item.label}</span>
                    </button>
                  );
                })}
              </div>
            );
          })}
        </nav>
      </aside>

      {sidebarCollapsed && <Tooltip target="[data-pr-tooltip]" />}

      {/* ─── Main Content Area ─── */}
      <div className="flex-1 flex flex-column" style={{ minWidth: 0, height: '100vh', overflow: 'hidden' }}>
        {/* Top Bar */}
        <header className="em-topbar flex align-items-center justify-content-between px-3" style={{ height: '48px' }} aria-label="Top bar">
          <div className="flex align-items-center gap-2">
            <span className="text-600" style={{ fontSize: '12px' }}><i className="pi pi-home" style={{ fontSize: '11px' }} /></span>
            {currentPage && (
              <>
                <span className="text-400" style={{ fontSize: '11px' }}>/</span>
                <span className="font-medium" style={{ fontSize: '12px', color: 'var(--color-text-primary)' }}>{currentPage}</span>
              </>
            )}
          </div>
          <div className="flex align-items-center gap-2">
            <Button icon="pi pi-bell" text severity="secondary" aria-label="Notifications"
              className="p-overlay-badge" style={{ width: '2rem', height: '2rem' }}>
              <Badge value="3" severity="danger" style={{ fontSize: '0.6rem', minWidth: '1rem', height: '1rem', lineHeight: '1rem' }} />
            </Button>
            <Menu model={userMenuItems} popup ref={userMenu} />
            <Button text onClick={(e) => userMenu.current?.toggle(e)} aria-label="User menu"
              className="flex align-items-center gap-1" style={{ padding: '0.25rem' }}>
              <Avatar label={user?.username?.charAt(0).toUpperCase() || 'U'} shape="circle" size="normal"
                style={{ background: 'var(--color-primary)', color: '#fff', width: '1.75rem', height: '1.75rem', fontSize: '0.75rem' }} />
              <span className="hidden lg:inline font-medium" style={{ color: 'var(--color-text-primary)', fontSize: '12px' }}>
                {user?.username}
              </span>
            </Button>
          </div>
        </header>

        {/* Page Content */}
        <main className="flex-1 p-3 overflow-y-auto">
          <Outlet />
        </main>
      </div>
    </div>
  );
};
