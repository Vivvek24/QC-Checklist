/**
 * Create Request Page — on format selection, fetches the checklist structure
 * and displays it as a beautiful checklist form.
 * Route: /qc-checklist/create-request
 *
 * Composition + JSX only — data loading, column-layout fetching, and
 * submit/draft persistence all live in useCreateRequest (see ../hooks).
 */

import { useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from 'primereact/button';
import { Dropdown } from 'primereact/dropdown';
import { Toast } from 'primereact/toast';
import { ProgressSpinner } from 'primereact/progressspinner';
import { useFormats } from '../../masters/hooks/useFormats';
import { ChecklistHeader } from '../components/ChecklistHeader';
import { TemplateDrivenSnip } from '../components/TemplateDrivenSnip';
import { AQLSnip } from '../components/AQLSnip';
import { ReconcilationSheetSnip } from '../components/ReconcilationSheetSnip';
import { ApprovalSnip } from '../components/ApprovalSnip';
import { FORMAT_TYPE, BASIC_DETAILS_STAGE } from '../../masters/constants';
import { useCreateRequest } from '../hooks/useCreateRequest';

export const CreateRequestPage = () => {
  const toast = useRef<Toast>(null);
  const navigate = useNavigate();
  const { data: formatsData, isLoading: formatsLoading } = useFormats();
  const [selectedFormatId, setSelectedFormatId] = useState<number | null>(null);

  const {
    loading,
    preview,
    expandedStages,
    stageColumns,
    snipRefs,
    handleFormatChange,
    toggleStage,
    handleSubmit,
    handleSaveAsDraft,
  } = useCreateRequest({
    onError: (detail) => toast.current?.show({ severity: 'error', summary: 'Error', detail, life: 5000 }),
    onSubmitSuccess: () =>
      toast.current?.show({ severity: 'success', summary: 'Submitted', detail: 'Checklist request submitted successfully.', life: 3000 }),
    onDraftSuccess: () =>
      toast.current?.show({ severity: 'success', summary: 'Saved', detail: 'Saved as draft successfully.', life: 3000 }),
  });

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

      {/* Format dropdown */}
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
            {preview.stages.filter((stage) => stage.status === 'Initial').map((stage, idx, filteredStages) => {
              const isExpanded = expandedStages[stage.format_stage_mapping_id] ?? false;
              return (
                <div key={stage.format_stage_mapping_id} style={{
                  marginBottom: idx < filteredStages.length - 1 ? '0.5rem' : 0,
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
                    <span style={{
                      fontWeight: 600, fontSize: '0.82rem',
                      color: isExpanded ? '#dc2626' : '#1e293b',
                    }}>
                      {stage.stage_name}
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
                        />
                      )}
                      {/* Approval section — not Basic Details */}
                      {stage.stage_name !== BASIC_DETAILS_STAGE && (
                        <>
                          <ApprovalSnip
                            questions={stage.questions}
                            approvalLabels={stage.approval_labels}
                            hasDeclarationQuestion={preview.has_declaration_question}
                          />

                          {/* Action buttons */}
                          <div style={{ borderTop: '1px solid #e2e8f0', marginTop: '0.5rem', padding: '0.75rem', background: '#fafbfc' }}
                            className="flex align-items-center justify-content-between">
                            <Button label="Save as Draft" icon="pi pi-save" severity="secondary" outlined size="small" type="button" onClick={handleSaveAsDraft} />
                            <Button label="Submit" icon="pi pi-check" size="small" type="button" onClick={handleSubmit} />
                          </div>
                        </>
                      )}
                    </div>
                  )}
                </div>
              );
            })}
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
