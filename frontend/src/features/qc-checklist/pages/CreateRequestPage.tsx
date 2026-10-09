/**
 * Create Request Page — composition + JSX only.
 *
 * All logic lives in hooks/helpers:
 *  - useCreateRequestPage: data loading, submit/approve/draft/refer-back,
 *    toasts, redirect, format options, entitlement, user-name resolution.
 *  - stageStatus: which stages show, their status label/colour, per-stage flags.
 * Route: /qc-checklist/create-request
 */

import { Button } from 'primereact/button';
import { Dropdown } from 'primereact/dropdown';
import { Toast } from 'primereact/toast';
import { Tag } from 'primereact/tag';
import { ProgressSpinner } from 'primereact/progressspinner';
import { ChecklistHeader } from '../components/ChecklistHeader';
import { TemplateDrivenSnip } from '../components/TemplateDrivenSnip';
import { ReconcilationSheetSnip } from '../components/ReconcilationSheetSnip';
import { ApprovalSnip } from '../components/ApprovalSnip';
import { FORMAT_TYPE, BASIC_DETAILS_STAGE } from '../../masters/constants';
import { useCreateRequestPage } from '../hooks/useCreateRequestPage';
import { deriveStageFlags, statusColor, statusLabel, visibleStages } from '../utils/stageStatus';

const cardSection = { borderTop: '1px solid #e2e8f0', marginTop: '0.5rem', padding: '0.75rem', background: '#fafbfc' };

export const CreateRequestPage = () => {
  const {
    toastRef, requestNumber, formatOptions, formatsLoading, selectedFormatId,
    canInitiate, userNameById, onFormatChange, goToDashboard,
    loading, preview, isContinuation, expandedStages, stageColumns,
    savedAnswersByFsm, approvalMappingsByFsm, submitting, snipRefs, approvalRefs,
    toggleStage, handleSubmit, handleSaveAsDraft, handleApprove, handleReferBack,
  } = useCreateRequestPage();

  const stages = preview ? visibleStages(preview.stages, isContinuation) : [];

  return (
    <div className="p-3">
      <Toast ref={toastRef} />

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
          Initiating a new request needs the initiate entitlement. */}
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
          <ChecklistHeader formatName={preview.format_name} formatNo={preview.format_no} unitName={preview.unit_name} />

          <div style={{ padding: '0.75rem 1rem' }}>
            {stages.length === 0 && isContinuation && (
              <div style={{ textAlign: 'center', padding: '2rem 1rem', color: '#64748b', fontSize: '0.88rem' }}>
                <i className="pi pi-info-circle" style={{ fontSize: '1.4rem', display: 'block', marginBottom: '0.5rem' }} />
                This request has no stages to show yet.
              </div>
            )}

            {stages.map((stage, idx) => {
              const fsmId = stage.format_stage_mapping_id;
              const isExpanded = expandedStages[fsmId] ?? false;
              const { isBasicDetails, isFillable, isApprovable, singleLabel } = deriveStageFlags(stage);
              return (
                <div key={fsmId} style={{
                  marginBottom: idx < stages.length - 1 ? '0.5rem' : 0,
                  border: `1px solid ${isExpanded ? '#fca5a5' : '#e2e8f0'}`,
                  borderRadius: '8px',
                  overflow: 'hidden',
                  transition: 'border-color 0.2s, box-shadow 0.2s',
                  boxShadow: isExpanded ? '0 2px 10px rgba(237,28,36,0.06)' : 'none',
                }}>
                  {/* Stage header */}
                  <div
                    onClick={() => toggleStage(fsmId)}
                    style={{
                      display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                      padding: '0.65rem 1rem', cursor: 'pointer',
                      background: isExpanded ? '#fef2f2' : 'transparent', transition: 'background 0.15s',
                    }}
                  >
                    <span style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                      <span style={{ fontWeight: 600, fontSize: '0.82rem', color: isExpanded ? '#dc2626' : '#1e293b' }}>
                        {stage.stage_name}
                      </span>
                      {stage.status && !isBasicDetails && (
                        <span style={{ fontWeight: 600, fontSize: '0.78rem', color: statusColor(stage.status) }}>
                          : {statusLabel(stage.status)}
                        </span>
                      )}
                    </span>
                    <i className={`pi ${isExpanded ? 'pi-chevron-up' : 'pi-chevron-down'}`}
                      style={{ fontSize: '0.7rem', color: isExpanded ? '#dc2626' : '#94a3b8' }} />
                  </div>

                  {/* Expanded — grid + approval */}
                  {isExpanded && (
                    <div style={{ borderTop: '1px solid #fca5a5' }}>
                      {preview.format_type === FORMAT_TYPE.RECONCILATION_SHEET ? (
                        <ReconcilationSheetSnip
                          ref={(el) => { snipRefs.current[fsmId] = el; }}
                          questions={stage.questions}
                          sections={stage.sections ?? []}
                          stageName={stage.stage_name}
                          stageStatus={stage.status}
                          hasSection={stage.has_section}
                        />
                      ) : (
                        <TemplateDrivenSnip
                          ref={(el) => { snipRefs.current[fsmId] = el; }}
                          questions={stage.questions}
                          columns={stageColumns[fsmId] ?? []}
                          sections={stage.sections ?? []}
                          hasSection={stage.has_section}
                          stageName={stage.stage_name}
                          stageStatus={stage.status}
                          savedAnswers={savedAnswersByFsm[fsmId]}
                        />
                      )}

                      {stage.stage_name !== BASIC_DETAILS_STAGE && (
                        <>
                          <ApprovalSnip
                            ref={(el) => { approvalRefs.current[fsmId] = el; }}
                            questions={stage.questions}
                            approvalLabels={stage.approval_labels}
                            hasDeclarationQuestion={preview.has_declaration_question}
                            mappings={approvalMappingsByFsm[fsmId]}
                            canAct={isFillable || isApprovable}
                            stageStatus={stage.status}
                            userNameById={userNameById}
                          />

                          {/* Action buttons — driven by label count + status:
                              • Single-label fillable → Approve (fill + approve)
                              • Multi-label  fillable → Save as Draft / Submit
                              • Pending (multi-label) → Approve / Refer Back */}
                          {isFillable && singleLabel && (
                            <div style={cardSection} className="flex align-items-center justify-content-end">
                              <Button label="Approve" icon="pi pi-check-circle" severity="success" size="small" type="button" onClick={() => handleApprove(fsmId)} />
                            </div>
                          )}
                          {isFillable && !singleLabel && (
                            <div style={cardSection} className="flex align-items-center justify-content-between">
                              <Button label="Save as Draft" icon="pi pi-save" severity="secondary" outlined size="small" type="button" onClick={() => handleSaveAsDraft(fsmId)} />
                              <Button label="Submit" icon="pi pi-check" size="small" type="button" onClick={() => handleSubmit(fsmId)} />
                            </div>
                          )}
                          {isApprovable && (
                            <div style={cardSection} className="flex align-items-center justify-content-between">
                              <Button label="Refer Back" icon="pi pi-replay" severity="warning" outlined size="small" type="button" onClick={() => handleReferBack(fsmId)} />
                              <Button label="Approve" icon="pi pi-check-circle" severity="success" size="small" type="button" onClick={() => handleApprove(fsmId)} />
                            </div>
                          )}
                        </>
                      )}
                    </div>
                  )}
                </div>
              );
            })}
          </div>

          <div style={{ padding: '0.75rem 1rem', borderTop: '1px solid #e2e8f0' }}>
            <Button label="Back" icon="pi pi-angle-double-left" severity="secondary" outlined size="small"
              onClick={goToDashboard} type="button" />
          </div>
        </div>
      )}
    </div>
  );
};
