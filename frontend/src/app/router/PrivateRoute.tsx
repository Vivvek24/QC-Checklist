/**
 * Protected route wrapper.
 * Redirects to /login if not authenticated.
 * Uses RBAC menu permissions for access control.
 */

import { Navigate, useLocation } from 'react-router-dom';
import { useAppSelector } from '@app/store';

interface PrivateRouteProps {
  children: React.ReactNode;
  /**
   * Menu key(s) required to reach the route. An array means *all* of them are
   * required, which is how a nested area is gated: the masters screens ask for
   * both the section key (`masters`) and their own (`masters.countries`), so
   * revoking the section hides every screen under it while revoking one child
   * hides only that screen.
   */
  menuKey?: string | string[];
  /**
   * Menu keys where *any one* grants access. Use for a page reachable through
   * more than one entitlement — e.g. the request page, which an initiator
   * reaches via `qc_checklist` and an approver via `qc_checklist_fill`.
   */
  menuKeyAnyOf?: string[];
}

export const PrivateRoute = ({ children, menuKey, menuKeyAnyOf }: PrivateRouteProps) => {
  const { isAuthenticated, isBootstrapping } = useAppSelector((state) => state.auth);
  const { menuKeys, isLoaded: rbacLoaded, isLoading: rbacLoading } = useAppSelector((state) => state.rbac);
  const location = useLocation();

  // While the session is being restored from the refresh cookie, don't decide yet.
  if (isBootstrapping) {
    return null;
  }

  if (!isAuthenticated) {
    sessionStorage.setItem('redirectAfterLogin', location.pathname);
    return <Navigate to="/login" replace />;
  }

  // If menu key(s) are specified, wait until RBAC has finished loading
  // before making an access decision — prevents a flash-redirect to /unauthorized
  // while permissions are still being fetched after login.
  if (menuKey || menuKeyAnyOf) {
    if (!rbacLoaded || rbacLoading) {
      return null;
    }
    const required = menuKey ? (Array.isArray(menuKey) ? menuKey : [menuKey]) : [];
    const hasAllRequired = required.every((key) => menuKeys.includes(key));
    const hasAnyOf = !menuKeyAnyOf || menuKeyAnyOf.some((key) => menuKeys.includes(key));
    if (!hasAllRequired || !hasAnyOf) {
      return <Navigate to="/unauthorized" replace />;
    }
  }

  return <>{children}</>;
};
