/**
 * Stage status helpers for the Create Request page.
 *
 * Centralizes the rules for how a checklist stage is presented and which
 * actions apply to it, so the page stays composition + JSX only.
 */

import { BASIC_DETAILS_STAGE } from '../../masters/constants';
import type { ChecklistStagePreview } from '../models/ChecklistPreview';

/** Stage statuses the current user can still fill in. */
export const FILLABLE_STATUSES = new Set(['Initial', 'Draft', 'ReferBack']);

/** Human-readable label for a stage status, shown as "Stage Name : Status". */
export const statusLabel = (status: string): string => {
  switch (status) {
    case 'Initial': return 'To Fill';
    case 'Draft': return 'Draft';
    case 'ReferBack': return 'Referred Back';
    case 'Pending': return 'Pending Approval';
    case 'Approved': return 'Approved';
    default: return status;
  }
};

/** Accent color for a stage status label. */
export const statusColor = (status: string): string => {
  switch (status) {
    case 'Approved': return '#16a34a';
    case 'ReferBack': return '#dc2626';
    case 'Pending': return '#2563eb';
    default: return '#d97706'; // Initial / Draft = to fill
  }
};

/** Per-stage flags that drive rendering + which action buttons appear. */
export interface StageFlags {
  isBasicDetails: boolean;
  /** Editable by the filling analyst (Initial/Draft/ReferBack). */
  isFillable: boolean;
  /** Submitted and awaiting the approver's action (approve / refer back). */
  isApprovable: boolean;
  /** Single approval label → fill + approve in one step (no separate submit). */
  singleLabel: boolean;
}

export const deriveStageFlags = (stage: ChecklistStagePreview): StageFlags => {
  const isBasicDetails = stage.stage_name === BASIC_DETAILS_STAGE;
  return {
    isBasicDetails,
    isFillable: FILLABLE_STATUSES.has(stage.status),
    isApprovable: stage.status === 'Pending' && !isBasicDetails,
    singleLabel: !isBasicDetails && stage.approval_labels.length === 1,
  };
};

/** Stages to show: in continuation mode every touched stage (view + edit);
 * for a brand-new request only the fillable ones. */
export const visibleStages = (
  stages: ChecklistStagePreview[], isContinuation: boolean,
): ChecklistStagePreview[] =>
  stages.filter((s) => (isContinuation ? s.status !== '' : FILLABLE_STATUSES.has(s.status)));
