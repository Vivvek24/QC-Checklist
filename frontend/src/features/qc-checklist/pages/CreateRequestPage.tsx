/**
 * Create Request Page — on format selection, fetches the checklist structure
 * and displays it as a beautiful checklist form.
 * Route: /qc-checklist/create-request
 *
 * Composition + JSX only — data loading, column-layout fetching, and
 * submit/draft persistence all live in useCreateRequest (see ../hooks).
 */

import { useEffect, useRef, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { Button } from 'primereact/button';
import { Dropdown } from 'primereact/dropdown';
import { Toast } from 'primereact/toast';
import { Tag } from 'primereact/tag';
import { ProgressSpinner } from 'primereact/progressspinner';
import { useFormats } from '../../masters/hooks/useFormats';
import { ChecklistHeader } from '../components/ChecklistHeader';
import { TemplateDrivenSnip } from '../components/TemplateDrivenSnip';
import { AQLSnip } from '../components/AQLSnip';
import { ReconcilationSheetSnip } from '../components/ReconcilationSheetSnip';
import { ApprovalSnip } from '../components/ApprovalSnip';
import { FORMAT_TYPE, BASIC_DETAILS_STAGE } from '../../masters/constants';
import { useCreateRequest } from '../hooks/useCreateRequest';
import { useMenuPermission } from '@core/rbac/usePermissions';
import { useUsers } from '../../user-management/hooks/useUsers';
import { useMemo } from 'react';

/** Stage statuses the current user can still fill in. */
const FILLABLE_STATUSES = new Set(['Initial', 'Draft', 'ReferBack']);

/** Human-readable label for a stage status, shown as "Stage Name : Status". */
const statusLabel = (status: string): string => {
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
const statusColor = (status: string): string => {
  switch (status) {
    case 'Approved': return '#16a34a';
    case 'ReferBack': return '#dc2626';
    case 'Pending': return '#2563eb';
    default: return '#d97706'; // Initial / Draft = to fill
  }
};

export const CreateRequestPage = () => {
  const toast = useRef<Toast>(null);
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const requestNumber = searchParams.get('request');
  const { data: formatsData, isLoading: formatsLoading } = useFormats();
  const [selectedFormatId, setSelectedFormatId] = useState<number | null>(null);
  // Only roles with the initiate entitlement may start a brand-new request.
  // Anyone with the fill/approve entitlement reaches the page via a ?request=
  // link from the dashboard to continue an existing one.
  const { canAccess: canInitiate } = useMenuPermission('qc_checklist');

  // Resolve an acting user's id to their display name on the UI (no API change).
  const { data: usersData } = useUsers(0, 500);
  const userNameById = useMemo(() => {
    const map = new Map<number, string>(
      (usersData?.users ?? []).map((u) => [u.id, u.employee_name || u.username])
    );
    return (userId: number) => map.get(userId) ?? `User #${userId}`;
  }, [usersData]);

  // Show the toast, then redirect to the dashboard. The hook keeps `submitting`
  // true through the delay so the loader overlay stays up until we navigate.
  const toastThenDashboard = (opts: { severity: 'success' | 'warn'; summary: string; detail: string }) => {
    toast.current?.show({ ...opts, life: 1500 });
    setTimeout(() => navigate('/dashboard'), 1200);
  };

  const {
    loading,
    preview,
    isContinuation,
    expandedStages,
    stageColumns,
    savedAnswersByFsm,
    approvalMappingsByFsm,
    submitting,
    snipRefs,
    approvalRefs,
    handleFormatChange,
    loadRequest,
    toggleStage,
    handleSubmit,
    handleSaveAsDraft,
    handleApprove,
    handleReferBack,
  } = useCreateRequest({
    onError: (detail) => toast.current?.show({ severity: 'error', summary: 'Error', detail, life: 5000 }),
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

  // Continuation mode: a ?request=<number> query param opens an existing
  // request to fill its next pending stage (from the dashboard action).
  useEffect(() => {
    if (requestNumber) {
      void loadRequest(requestNumber);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [requestNumber]);

  const formatOptions = (formatsData?.items ?? []).map((f) => ({
    label: f.format_name,
    value: Number(f.id),
  }));

  const onFormatChange = (formatId: number | null) => {
    setSelectedFormatId(formatId);
    void handleFormatChange(formatId);
  };

  return (
    <div className="p-3">
      <Toast ref={toast} />

      {/* Full-page loader while an action is processing + redirecting. */}
      {submitting && (
        <div style={{
          position: 'fixed', inset: 0, zIndex: 2000,
          background: 'rgba(255,255,255,0.6)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
        }}>
          <ProgressSpinner style={{ width: '48px', height: '48px' }} strokeWidth="3" />
        </div>
      )}

      {/* Format dropdown — hidden in continuation mode (format is fixed).
          Initiating a new request needs the initiate entitlement; approvers
          who only have fill/approve access land here via a ?request= link. */}
      {isContinuation ? (
        <div className="mb-4 flex align-items-center gap-2">
          <span className="font-bold text-sm" style={{ color: '#374151' }}>Continuing Request</span>
          <Tag value={requestNumber ?? ''} severity="info" />
        </div>
      ) : canInitiate ? (
        <div className="mb-4">
          <label className="font-bold text-sm mb-2 block" style={{ color: '#374151' }}>Select Format</label>
          <Dropdown
            value={selectedFormatId}
            options={formatOptions}
            onChange={(e) => onFormatChange(e.value)}
            placeholder="Select Format"
            filter
            showClear
            loading={formatsLoading}
            style={{ width: '420px' }}
          />
        </div>
      ) : (
        <div style={{ textAlign: 'center', padding: '2.5rem 1rem', color: '#64748b', fontSize: '0.9rem' }}>
          <i className="pi pi-info-circle" style={{ fontSize: '1.6rem', display: 'block', marginBottom: '0.6rem' }} />
          You don't have access to initiate a new request. Open a request from the dashboard to fill or approve it.
        </div>
      )}

      {/* Loading */}
      {loading && (
        <div className="flex align-items-center justify-content-center py-5">
          <ProgressSpinner style={{ width: '40px', height: '40px' }} strokeWidth="3" />
        </div>
      )}

      {/* Checklist Form */}
      {preview && !loading && (
        <div className="qc-checklist-card">

          {/* ─── Header ─── */}
          <ChecklistHeader formatName={preview.format_name} formatNo={preview.format_no} unitName={preview.unit_name} />

          {/* ─── Stages ─── */}
          <div style={{ padding: '0.75rem 1rem' }}>
            {(() => {
              // In continuation mode, show every stage that has been touched
              // (any non-empty status) so the page acts as a view (read-only
              // for submitted/approved stages) and create (editable for
              // fillable stages). In new-request mode, only fillable stages.
              const visibleStages = preview.stages.filter((stage) =>
                isContinuation ? stage.status !== '' : FILLABLE_STATUSES.has(stage.status)
              );
              if (visibleStages.length === 0 && isContinuation) {
                return (
                  <div style={{
                    textAlign: 'center', padding: '2rem 1rem',
                    color: '#64748b', fontSize: '0.88rem',
                  }}>
                    <i className="pi pi-info-circle" style={{ fontSize: '1.4rem', display: 'block', marginBottom: '0.5rem' }} />
                    This request has no stages to show yet.
                  </div>
                );
              }
              return visibleStages.map((stage, idx) => {
              const isExpanded = expandedStages[stage.format_stage_mapping_id] ?? false;
              const isFillable = FILLABLE_STATUSES.has(stage.status);
              const isBasicDetails = stage.stage_name === BASIC_DETAILS_STAGE;
              // A submitted (Pending) stage is awaiting approval: the approver
              // acts on it here (approve / refer back). Basic Details is never
              // approved on its own.
              const isApprovable = stage.status === 'Pending' && !isBasicDetails;
              // Single-label stages skip the separate submit step: the one
              // actor fills the data and approves directly.
              const singleLabel = !isBasicDetails && stage.approval_labels.length === 1;
              return (
                <div key={stage.format_stage_mapping_id} style={{
                  marginBottom: idx < visibleStages.length - 1 ? '0.5rem' : 0,
                  border: `1px solid ${isExpanded ? '#fca5a5' : '#e2e8f0'}`,
                  borderRadius: '8px',
                  overflow: 'hidden',
                  transition: 'border-color 0.2s, box-shadow 0.2s',
                  boxShadow: isExpanded ? '0 2px 10px rgba(237,28,36,0.06)' : 'none',
                }}>
                  {/* Stage header */}
                  <div
                    onClick={() => toggleStage(stage.format_stage_mapping_id)}
                    style={{
                      display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                      padding: '0.65rem 1rem',
                      cursor: 'pointer',
                      background: isExpanded ? '#fef2f2' : 'transparent',
                      transition: 'background 0.15s',
                    }}
                  >
                    <span style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                      <span style={{
                        fontWeight: 600, fontSize: '0.82rem',
                        color: isExpanded ? '#dc2626' : '#1e293b',
                      }}>
                        {stage.stage_name}
                      </span>
                      {stage.status && !isBasicDetails && (
                        <span style={{
                          fontWeight: 600, fontSize: '0.78rem',
                          color: statusColor(stage.status),
                        }}>
                          : {statusLabel(stage.status)}
                        </span>
                      )}
                    </span>
                    <i className={`pi ${isExpanded ? 'pi-chevron-up' : 'pi-chevron-down'}`}
                      style={{ fontSize: '0.7rem', color: isExpanded ? '#dc2626' : '#94a3b8' }} />
                  </div>

                  {/* Expanded — grid */}
                  {isExpanded && (
                    <div style={{ borderTop: '1px solid #fca5a5' }}>
                      {preview.format_type === FORMAT_TYPE.AQL ? (
                        <AQLSnip
                          questions={stage.questions}
                          sections={stage.sections ?? []}
                          stageName={stage.stage_name}
                          stageStatus={stage.status}
                          hasSection={stage.has_section}
                        />
                      ) : preview.format_type === FORMAT_TYPE.RECONCILATION_SHEET ? (
                        <ReconcilationSheetSnip
                          ref={(el) => { snipRefs.current[stage.format_stage_mapping_id] = el; }}
                          questions={stage.questions}
                          sections={stage.sections ?? []}
                          stageName={stage.stage_name}
                          stageStatus={stage.status}
                          hasSection={stage.has_section}
                        />
                      ) : (
                        <TemplateDrivenSnip
                          ref={(el) => { snipRefs.current[stage.format_stage_mapping_id] = el; }}
                          questions={stage.questions}
                          columns={stageColumns[stage.format_stage_mapping_id] ?? []}
                          stageName={stage.stage_name}
                          stageStatus={stage.status}
                          savedAnswers={savedAnswersByFsm[stage.format_stage_mapping_id]}
                        />
                      )}
                      {/* Approval section — not Basic Details */}
                      {stage.stage_name !== BASIC_DETAILS_STAGE && (
                        <>
                          <ApprovalSnip
                            ref={(el) => { approvalRefs.current[stage.format_stage_mapping_id] = el; }}
                            questions={stage.questions}
                            approvalLabels={stage.approval_labels}
                            hasDeclarationQuestion={preview.has_declaration_question}
                            mappings={approvalMappingsByFsm[stage.format_stage_mapping_id]}
                            canAct={isFillable || isApprovable}
                            stageStatus={stage.status}
                            userNameById={userNameById}
                          />

                          {/* Action buttons — driven by label count + stage status:
                              • Single-label fillable  → Approve (fill + approve in one step)
                              • Multi-label  fillable  → Save as Draft / Submit
                              • Pending (multi-label)  → Approve / Refer Back */}
                          {isFillable && singleLabel && (
                            <div style={{ borderTop: '1px solid #e2e8f0', marginTop: '0.5rem', padding: '0.75rem', background: '#fafbfc' }}
                              className="flex align-items-center justify-content-end">
                              <Button label="Approve" icon="pi pi-check-circle" severity="success" size="small" type="button" onClick={() => handleApprove(stage.format_stage_mapping_id)} />
                            </div>
                          )}
                          {isFillable && !singleLabel && (
                            <div style={{ borderTop: '1px solid #e2e8f0', marginTop: '0.5rem', padding: '0.75rem', background: '#fafbfc' }}
                              className="flex align-items-center justify-content-between">
                              <Button label="Save as Draft" icon="pi pi-save" severity="secondary" outlined size="small" type="button" onClick={() => handleSaveAsDraft(stage.format_stage_mapping_id)} />
                              <Button label="Submit" icon="pi pi-check" size="small" type="button" onClick={() => handleSubmit(stage.format_stage_mapping_id)} />
                            </div>
                          )}
                          {isApprovable && (
                            <div style={{ borderTop: '1px solid #e2e8f0', marginTop: '0.5rem', padding: '0.75rem', background: '#fafbfc' }}
                              className="flex align-items-center justify-content-between">
                              <Button label="Refer Back" icon="pi pi-replay" severity="warning" outlined size="small" type="button" onClick={() => handleReferBack(stage.format_stage_mapping_id)} />
                              <Button label="Approve" icon="pi pi-check-circle" severity="success" size="small" type="button" onClick={() => handleApprove(stage.format_stage_mapping_id)} />
                            </div>
                          )}
                        </>
                      )}
                    </div>
                  )}
                </div>
              );
            });
            })()}
          </div>

          {/* ─── Footer ─── */}
          <div style={{
            padding: '0.75rem 1rem',
            borderTop: '1px solid #e2e8f0',
          }}>
            <Button label="Back" icon="pi pi-angle-double-left" severity="secondary" outlined size="small"
              onClick={() => navigate('/dashboard')} type="button" />
          </div>
        </div>
      )}
    </div>
  );
};
