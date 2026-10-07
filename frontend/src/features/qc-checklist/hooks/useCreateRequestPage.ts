/**
 * useCreateRequestPage — the Create Request page's controller.
 *
 * Wires useChecklistWorkflow to the page's concerns (toasts, redirect-to-dashboard
 * after an action, format dropdown options, continuation-mode auto-load, and
 * the initiate-vs-fill entitlement) so the page component stays composition +
 * JSX only.
 */

import { useEffect, useRef, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import type { Toast } from 'primereact/toast';
import { useFormats } from '../../masters/hooks/useFormats';
import { useMenuPermission } from '@core/rbac/usePermissions';
import { useChecklistWorkflow, type UseChecklistWorkflowResult } from './useChecklistWorkflow';
import { useUserNameResolver } from './useUserNameResolver';

export interface UseCreateRequestPageResult extends UseChecklistWorkflowResult {
  toastRef: React.RefObject<Toast | null>;
  /** The ?request= number when opened in continuation mode (else null). */
  requestNumber: string | null;
  /** Options for the format dropdown. */
  formatOptions: { label: string; value: number }[];
  formatsLoading: boolean;
  selectedFormatId: number | null;
  /** True when the user may initiate a brand-new request. */
  canInitiate: boolean;
  /** Resolves an acting user's id to a display name. */
  userNameById: (userId: number) => string;
  onFormatChange: (formatId: number | null) => void;
  goToDashboard: () => void;
}

export const useCreateRequestPage = (): UseCreateRequestPageResult => {
  const toastRef = useRef<Toast>(null);
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const requestNumber = searchParams.get('request');

  const { data: formatsData, isLoading: formatsLoading } = useFormats();
  const [selectedFormatId, setSelectedFormatId] = useState<number | null>(null);
  const { canAccess: canInitiate } = useMenuPermission('qc_checklist');
  const userNameById = useUserNameResolver();

  // Show the toast, then redirect to the dashboard. The hook keeps `submitting`
  // true through the delay so the loader overlay stays up until we navigate.
  const toastThenDashboard = (opts: { severity: 'success' | 'warn'; summary: string; detail: string }) => {
    toastRef.current?.show({ ...opts, life: 1500 });
    setTimeout(() => navigate('/dashboard'), 1200);
  };

  const workflow = useChecklistWorkflow({
    onError: (detail) =>
      toastRef.current?.show({ severity: 'error', summary: 'Error', detail, life: 5000 }),
    onSubmitSuccess: () =>
      toastThenDashboard({ severity: 'success', summary: 'Submitted', detail: 'Checklist request submitted successfully.' }),
    onDraftSuccess: () =>
      toastThenDashboard({ severity: 'success', summary: 'Saved', detail: 'Saved as draft successfully.' }),
    onApproveSuccess: (fullyApproved) =>
      toastThenDashboard({
        severity: 'success', summary: 'Approved',
        detail: fullyApproved ? 'Request fully approved!' : 'Stage approved successfully.',
      }),
    onReferBackSuccess: () =>
      toastThenDashboard({ severity: 'warn', summary: 'Referred Back', detail: 'Stage referred back to analyst.' }),
  });

  // Continuation mode: a ?request=<number> param opens an existing request.
  useEffect(() => {
    if (requestNumber) {
      void workflow.loadRequest(requestNumber);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [requestNumber]);

  const formatOptions = (formatsData?.items ?? []).map((f) => ({
    label: f.format_name,
    value: Number(f.id),
  }));

  const onFormatChange = (formatId: number | null) => {
    setSelectedFormatId(formatId);
    void workflow.handleFormatChange(formatId);
  };

  return {
    ...workflow,
    toastRef,
    requestNumber,
    formatOptions,
    formatsLoading,
    selectedFormatId,
    canInitiate,
    userNameById,
    onFormatChange,
    goToDashboard: () => navigate('/dashboard'),
  };
};
