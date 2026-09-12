/**
 * Protected route wrapper.
 * Redirects to /login if not authenticated.
 * Uses RBAC menu permissions for access control.
 */

import { Navigate, useLocation } from 'react-router-dom';

import { useAppSelector } from '@app/store';

interface PrivateRouteProps {
  children: React.ReactNode;
  menuKey?: string;
}

export const PrivateRoute = ({ children, menuKey }: PrivateRouteProps) => {
  const { isAuthenticated, isBootstrapping } = useAppSelector((state) => state.auth);
  const { menuKeys, isLoaded: rbacLoaded } = useAppSelector((state) => state.rbac);
  const location = useLocation();

  // While the session is being restored from the refresh cookie, don't decide
  // yet — avoids a premature bounce to /login on reload.
  if (isBootstrapping) {
    return null;
  }

  if (!isAuthenticated) {
    // Save intended destination
    sessionStorage.setItem('redirectAfterLogin', location.pathname);
    return <Navigate to="/login" replace />;
  }

  // If a menuKey is specified, check RBAC permissions
  if (menuKey) {
    if (!rbacLoaded) {
      // Still loading permissions — show nothing briefly
      return null;
    }
    if (!menuKeys.includes(menuKey)) {
      return <Navigate to="/unauthorized" replace />;
    }
  }

  return <>{children}</>;
};
