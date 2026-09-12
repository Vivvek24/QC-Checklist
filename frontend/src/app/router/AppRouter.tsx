/**
 * Application router.
 * Defines all routes with authentication and RBAC guards.
 */

import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';

import { MainLayout } from '@app/layouts/MainLayout';

import { LoginPage } from '@features/authentication/pages/LoginPage';
import { MicrosoftCallbackPage } from '@features/authentication/pages/MicrosoftCallbackPage';
import { DashboardPage } from '@features/dashboard';
import { EmployeeDirectoryPage } from '@features/employee-directory';
import { PublishedDarwinAdPage, PublishedEsignerPage } from '@features/published-services';
import { AuditLogsPage } from '@features/rbac-admin/pages/AuditLogsPage';
import { RolesPage } from '@features/rbac-admin/pages/RolesPage';
import { DarwinboxServicePage } from '@features/service-menu/pages/DarwinboxServicePage';
import { EmployeeADServicePage } from '@features/service-menu/pages/EmployeeADServicePage';
import { EncryptionServicePage } from '@features/service-menu/pages/EncryptionServicePage';
import { EsignerServicePage } from '@features/service-menu/pages/EsignerServicePage';
import { LdapServersPage } from '@features/service-menu/pages/LdapServersPage';
import { LdapServicePage } from '@features/service-menu/pages/LdapServicePage';
import { UserListPage } from '@features/user-management/pages/UserListPage';

import { NotFoundPage } from '@shared/components/NotFoundPage';

import { AuthBootstrap } from './AuthBootstrap';
import { PrivateRoute } from './PrivateRoute';

export const AppRouter = () => {
  return (
    <BrowserRouter>
      <AuthBootstrap>
        <Routes>
          {/* Public routes */}
          <Route path="/login" element={<LoginPage />} />
          <Route path="/auth/microsoft/callback" element={<MicrosoftCallbackPage />} />

          {/* Protected routes with layout */}
          <Route
            path="/"
            element={
              <PrivateRoute>
                <MainLayout />
              </PrivateRoute>
            }
          >
            <Route index element={<Navigate to="/dashboard" replace />} />
            <Route path="dashboard" element={<DashboardPage />} />
            <Route
              path="employees"
              element={
                <PrivateRoute menuKey="employees">
                  <EmployeeDirectoryPage />
                </PrivateRoute>
              }
            />
            <Route
              path="users"
              element={
                <PrivateRoute menuKey="users">
                  <UserListPage />
                </PrivateRoute>
              }
            />
            <Route
              path="roles"
              element={
                <PrivateRoute menuKey="roles">
                  <RolesPage />
                </PrivateRoute>
              }
            />
            <Route
              path="audit-logs"
              element={
                <PrivateRoute menuKey="audit_logs">
                  <AuditLogsPage />
                </PrivateRoute>
              }
            />
            <Route
              path="services/employee-ad"
              element={
                <PrivateRoute menuKey="services">
                  <EmployeeADServicePage />
                </PrivateRoute>
              }
            />
            <Route
              path="services/darwinbox"
              element={
                <PrivateRoute menuKey="services">
                  <DarwinboxServicePage />
                </PrivateRoute>
              }
            />
            <Route
              path="ldap-servers"
              element={
                <PrivateRoute menuKey="ldap">
                  <LdapServersPage />
                </PrivateRoute>
              }
            />
            <Route
              path="services/ldap"
              element={
                <PrivateRoute menuKey="services">
                  <LdapServicePage />
                </PrivateRoute>
              }
            />
            <Route
              path="services/esigner"
              element={
                <PrivateRoute menuKey="services">
                  <EsignerServicePage />
                </PrivateRoute>
              }
            />
            <Route
              path="services/encryption"
              element={
                <PrivateRoute menuKey="services">
                  <EncryptionServicePage />
                </PrivateRoute>
              }
            />
            <Route
              path="published-services/darwin-ad"
              element={
                <PrivateRoute menuKey="published_services">
                  <PublishedDarwinAdPage />
                </PrivateRoute>
              }
            />
            <Route
              path="published-services/esigner"
              element={
                <PrivateRoute menuKey="published_services">
                  <PublishedEsignerPage />
                </PrivateRoute>
              }
            />
            {/* 404 for any other path while authenticated — stays inside the app shell */}
            <Route path="*" element={<NotFoundPage />} />
          </Route>

          {/* Unauthorized */}
          <Route
            path="/unauthorized"
            element={
              <div className="flex align-items-center justify-content-center min-h-screen">
                <div className="text-center">
                  <h1 className="text-4xl text-red-500">403</h1>
                  <p className="text-600">You don't have permission to access this page.</p>
                </div>
              </div>
            }
          />

          {/*
          No top-level catch-all: unknown paths fall through to the protected
          "/" route, which shows the in-app 404 when authenticated or redirects
          to /login (via PrivateRoute) when not. This prevents unknown URLs from
          logging authenticated users out.
        */}
        </Routes>
      </AuthBootstrap>
    </BrowserRouter>
  );
};
