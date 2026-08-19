/**
 * Application router.
 */

import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { LoginPage } from '@features/authentication/pages/LoginPage';
import { MicrosoftCallbackPage } from '@features/authentication/pages/MicrosoftCallbackPage';
import { UserListPage } from '@features/user-management/pages/UserListPage';
import { EmployeeADServicePage } from '@features/service-menu/pages/EmployeeADServicePage';
import { RolesPage } from '@features/rbac-admin/pages/RolesPage';
import { AuditLogsPage } from '@features/rbac-admin/pages/AuditLogsPage';
import {
  WorkflowDefinitionsPage,
  WorkflowBuilderPage,
  ApprovalMatrixPage,
} from '@features/workflow-admin';
import { BusinessUnitPage, UnitPage, FormatPage, StagePage, QuestionPage, ProductPage, ValidationTypePage, RemarkPage, SapFieldPage, ApprovalLabelPage, FormatStagesPage, FormatsViewPage, StageQuestionViewPage, ProductTestsPage } from '@features/masters';
import { CreateRequestPage } from '@features/qc-checklist';
import { DashboardPage } from '@features/dashboard';
import { MainLayout } from '@app/layouts/MainLayout';
import { PrivateRoute } from './PrivateRoute';
import { AuthBootstrap } from './AuthBootstrap';
import { NotFoundPage } from '@shared/components/NotFoundPage';

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
            <Route
              path="dashboard"
              element={
                <PrivateRoute menuKey="dashboard">
                  <DashboardPage />
                </PrivateRoute>
              }
            />
            <Route
              path="qc-checklist/create-request"
              element={
                <PrivateRoute menuKey="qc_checklist">
                  <CreateRequestPage />
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

            {/* ─── Masters ─── */}
            <Route
              path="masters/business-units"
              element={
                <PrivateRoute menuKey={['masters', 'masters.business_units']}>
                  <BusinessUnitPage />
                </PrivateRoute>
              }
            />
            <Route
              path="masters/units"
              element={
                <PrivateRoute menuKey={['masters', 'masters.units']}>
                  <UnitPage />
                </PrivateRoute>
              }
            />
            <Route
              path="masters/formats"
              element={
                <PrivateRoute menuKey={['masters', 'masters.formats']}>
                  <FormatPage />
                </PrivateRoute>
              }
            />
            <Route
              path="masters/stages"
              element={
                <PrivateRoute menuKey={['masters', 'masters.stages']}>
                  <StagePage />
                </PrivateRoute>
              }
            />
            <Route
              path="masters/questions"
              element={
                <PrivateRoute menuKey={['masters', 'masters.questions']}>
                  <QuestionPage />
                </PrivateRoute>
              }
            />
            <Route
              path="masters/products"
              element={
                <PrivateRoute menuKey={['masters', 'masters.products']}>
                  <ProductPage />
                </PrivateRoute>
              }
            />
            <Route
              path="masters/products/:productId/tests"
              element={
                <PrivateRoute menuKey={['masters', 'masters.products']}>
                  <ProductTestsPage />
                </PrivateRoute>
              }
            />
            <Route
              path="masters/validation-types"
              element={
                <PrivateRoute menuKey={['masters', 'masters.validation_types']}>
                  <ValidationTypePage />
                </PrivateRoute>
              }
            />
            <Route
              path="masters/remarks"
              element={
                <PrivateRoute menuKey={['masters', 'masters.remarks']}>
                  <RemarkPage />
                </PrivateRoute>
              }
            />
            <Route
              path="masters/sap-fields"
              element={
                <PrivateRoute menuKey={['masters', 'masters.sap_fields']}>
                  <SapFieldPage />
                </PrivateRoute>
              }
            />
            <Route
              path="masters/approval-labels"
              element={
                <PrivateRoute menuKey={['masters', 'masters.approval_labels']}>
                  <ApprovalLabelPage />
                </PrivateRoute>
              }
            />
            <Route
              path="masters/stage-question-mapping/:formatId/stages"
              element={
                <PrivateRoute menuKey={['masters', 'masters.stage_question_mapping']}>
                  <FormatStagesPage />
                </PrivateRoute>
              }
            />
            <Route
              path="masters/formats-view"
              element={
                <PrivateRoute menuKey={['masters', 'masters.formats_view']}>
                  <FormatsViewPage />
                </PrivateRoute>
              }
            />
            <Route
              path="masters/formats-view/:formatId/stages"
              element={
                <PrivateRoute menuKey={['masters', 'masters.formats_view']}>
                  <FormatStagesPage />
                </PrivateRoute>
              }
            />
            <Route
              path="masters/formats-view/:formatId/questions"
              element={
                <PrivateRoute menuKey={['masters', 'masters.formats_view']}>
                  <StageQuestionViewPage />
                </PrivateRoute>
              }
            />

            {/* ─── Workflow engine ─── */}
            <Route
              path="workflows"
              element={
                <PrivateRoute menuKey="workflows">
                  <WorkflowDefinitionsPage />
                </PrivateRoute>
              }
            />
            <Route
              path="workflows/:definitionId"
              element={
                <PrivateRoute menuKey="workflows">
                  <WorkflowBuilderPage />
                </PrivateRoute>
              }
            />
            <Route
              path="approval-matrix"
              element={
                <PrivateRoute menuKey="workflows">
                  <ApprovalMatrixPage />
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
            <Route path="*" element={<NotFoundPage />} />
          </Route>

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
        </Routes>
      </AuthBootstrap>
    </BrowserRouter>
  );
};
