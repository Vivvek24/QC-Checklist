/**
 * Dashboard landing page.
 *
 * Renders quick-access tiles for every navigable page the user can reach,
 * grouped by section and filtered by RBAC menu permissions (so a tile only
 * appears when the user is allowed to open the target route). Tiles reuse the
 * shared navigation config, so they stay in sync with the sidebar.
 */

import { Card } from 'primereact/card';
import { useNavigate } from 'react-router-dom';

import { NAV_ITEMS, filterNavItemsByRbac, groupNavItemsBySection } from '@app/navigation/navConfig';
import { useAppSelector } from '@app/store';

import { useMenuPermissions } from '@core/rbac/usePermissions';

export const DashboardPage = () => {
  const navigate = useNavigate();
  const { user } = useAppSelector((state) => state.auth);
  const { menuKeys, isLoaded: rbacLoaded } = useMenuPermissions();

  // Exclude the Dashboard tile itself; keep only RBAC-allowed destinations.
  const tiles = filterNavItemsByRbac(
    NAV_ITEMS.filter((item) => item.path !== '/dashboard'),
    menuKeys,
    rbacLoaded,
  );
  const sections = groupNavItemsBySection(tiles);

  return (
    <div className="p-4">
      <div className="mb-4">
        <h2 className="text-2xl font-semibold text-900 m-0">
          Welcome{user?.username ? `, ${user.username}` : ''}
        </h2>
        <p className="text-600 mt-1 mb-0">Jump to any area you have access to.</p>
      </div>

      {Object.entries(sections).length === 0 ? (
        <p className="text-600">You don't have access to any pages yet.</p>
      ) : (
        Object.entries(sections).map(([section, items]) => (
          <div key={section} className="mb-4">
            <div
              className="text-xs font-semibold uppercase mb-2"
              style={{ color: 'var(--color-text-muted)', letterSpacing: '0.05em' }}
            >
              {section}
            </div>
            <div className="grid">
              {items.map((item) => (
                <div key={item.path} className="col-12 sm:col-6 lg:col-4 xl:col-3">
                  <Card
                    className="cursor-pointer h-full transition-all transition-duration-200 hover:shadow-4"
                    onClick={() => navigate(item.path)}
                    role="button"
                    aria-label={`Go to ${item.label}`}
                  >
                    <div className="flex align-items-start gap-3">
                      <span
                        className="flex align-items-center justify-content-center border-round flex-shrink-0"
                        style={{
                          width: '2.5rem',
                          height: '2.5rem',
                          background: 'var(--color-primary-50)',
                          color: 'var(--color-primary)',
                        }}
                      >
                        <i className={item.icon} style={{ fontSize: '1.1rem' }} />
                      </span>
                      <div className="flex flex-column">
                        <span className="font-semibold text-900">{item.label}</span>
                        {item.description && (
                          <span className="text-600 text-sm mt-1">{item.description}</span>
                        )}
                      </div>
                    </div>
                  </Card>
                </div>
              ))}
            </div>
          </div>
        ))
      )}
    </div>
  );
};
