/**
 * Create Request Page — on format selection, fetches the checklist structure
 * and displays it as a beautiful checklist form.
 * Route: /qc-checklist/create-request
 */

import { useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from 'primereact/button';
import { Dropdown } from 'primereact/dropdown';
import { Toast } from 'primereact/toast';
import { ProgressSpinner } from 'primereact/progressspinner';
import { apiClient } from '@shared/services/apiClient';
import { useFormats } from '../../masters/hooks/useFormats';
import { ChecklistHeader } from '../components/ChecklistHeader';
import { ChromatographicSnip, type ChromatographicSnipHandle } from '../components/ChromatographicSnip';
import { AQLSnip } from '../components/AQLSnip';
import { ReconcilationSheetSnip, type ReconcilationSheetSnipHandle } from '../components/ReconcilationSheetSnip';
import { ApprovalSnip } from '../components/ApprovalSnip';
import { FORMAT_TYPE } from '../../masters/constants';

interface QuestionAnswerPreview {
  stage_question_mapping_id: number;
  question_id: number;
  question_title: string;
  serial_number: number;
  section_id: number | null;
  section_name: string | null;
  show_on_grid: boolean;
  answer_type: string;
  has_text_box: boolean;
  has_multiple_text_box: boolean;
  has_sub_question: boolean;
  is_declaration_question: boolean;
  aql_limit: string;
  sub_questions: QuestionAnswerPreview[];
  options: { id: number; label: string }[];
  response_options: { id: number; label: string }[];
}

interface ApprovalLabelPreview {
  approval_label_id: number;
  label: string;
}

interface ChecklistStagePreview {
  format_stage_mapping_id: number;
  stage_id: number;
  stage_name: string;
  is_approvable: boolean;
  has_section: boolean;
  status: string;
  questions: QuestionAnswerPreview[];
  sections: SectionPreview[];
  approval_labels: ApprovalLabelPreview[];
}

interface SectionPreview {
  section_id: number;
  section_name: string;
  questions: QuestionAnswerPreview[];
}

interface ChecklistPreview {
  format_id: number;
  format_name: string;
  format_no: string;
  format_type: string;
  has_declaration_question: boolean;
  unit_name: string;
  stages: ChecklistStagePreview[];
}

export const CreateRequestPage = () => {
  const toast = useRef<Toast>(null);
  const navigate = useNavigate();
  const { data: formatsData, isLoading: formatsLoading } = useFormats();

  const [selectedFormatId, setSelectedFormatId] = useState<number | null>(null);
  const [loading, setLoading] = useState(false);
  const [preview, setPreview] = useState<ChecklistPreview | null>(null);
  const [expandedStages, setExpandedStages] = useState<Record<number, boolean>>({});
  const snipRefs = useRef<Record<number, ChromatographicSnipHandle | ReconcilationSheetSnipHandle | null>>({});

  const formatOptions = (formatsData?.items ?? []).map((f) => ({
    label: f.format_name,
    value: Number(f.id),
  }));

  const handleFormatChange = async (formatId: number | null) => {
    setSelectedFormatId(formatId);
    if (!formatId) {
      setPreview(null);
      setExpandedStages({});
      return;
    }
    setLoading(true);
    setPreview(null);
    setExpandedStages({});
    try {
      const { data } = await apiClient.get<ChecklistPreview>('/qc-checklist/preview', {
        params: { format_id: formatId },
      });
      setPreview(data);
    } catch (e: any) {
      toast.current?.show({ severity: 'error', summary: 'Error', detail: e?.response?.data?.detail || 'Failed to load checklist', life: 5000 });
    } finally {
      setLoading(false);
    }
  };

  const toggleStage = (fsmId: number) => {
    setExpandedStages((prev) => ({ ...prev, [fsmId]: !prev[fsmId] }));
  };

  const handleSubmit = async () => {
    if (!preview) return;

    // Validate all stage snips
    let allValid = true;
    for (const key of Object.keys(snipRefs.current)) {
      const ref = snipRefs.current[Number(key)];
      if (ref) {
        const valid = ref.validate();
        if (!valid) allValid = false;
      }
    }
    if (!allValid) {
      toast.current?.show({ severity: 'warn', summary: 'Validation Failed', detail: 'Please fill all required fields.', life: 4000 });
      return;
    }

    // Submit only the first Initial stage (the one being filled)
    const stage = preview.stages.find((s) => s.status === 'Initial');
    if (!stage) return;

    const ref = snipRefs.current[stage.format_stage_mapping_id];
    const answers = ref?.getAnswers() || [];

    try {
      await apiClient.post('/qc-checklist/submit-stage', {
        checklist_request_id: null,
        format_id: preview.format_id,
        checklist_stage_id: null,
        format_stage_mapping_id: stage.format_stage_mapping_id,
        action: 'submit',
        remark_id: null,
        remark_text: '',
        answers: answers.map((a) => ({
          stage_question_mapping_id: a.stage_question_mapping_id,
          question_id: a.question_id,
          textbox_value: a.textbox_value,
          question_option_id: a.question_option_id,
          response_answer: a.response_answer,
          product_id: (a as any).product_id || null,
          date_time: (a as any).date_time || null,
          helpers: a.helpers.length > 0 ? a.helpers : null,
        })),
      });
      toast.current?.show({ severity: 'success', summary: 'Submitted', detail: 'Checklist request submitted successfully.', life: 3000 });
    } catch (e: any) {
      toast.current?.show({ severity: 'error', summary: 'Error', detail: e?.response?.data?.detail || 'Submit failed', life: 5000 });
    }
  };

  const handleSaveAsDraft = async () => {
    if (!preview) return;

    const stage = preview.stages.find((s) => s.status === 'Initial');
    if (!stage) return;

    const ref = snipRefs.current[stage.format_stage_mapping_id];
    const answers = ref?.getAnswers() || [];

    try {
      await apiClient.post('/qc-checklist/submit-stage', {
        checklist_request_id: null,
        format_id: preview.format_id,
        checklist_stage_id: null,
        format_stage_mapping_id: stage.format_stage_mapping_id,
        action: 'save_draft',
        remark_id: null,
        remark_text: '',
        answers: answers.map((a) => ({
          stage_question_mapping_id: a.stage_question_mapping_id,
          question_id: a.question_id,
          textbox_value: a.textbox_value,
          question_option_id: a.question_option_id,
          response_answer: a.response_answer,
          product_id: (a as any).product_id || null,
          date_time: (a as any).date_time || null,
          helpers: a.helpers.length > 0 ? a.helpers : null,
        })),
      });
      toast.current?.show({ severity: 'success', summary: 'Saved', detail: 'Saved as draft successfully.', life: 3000 });
    } catch (e: any) {
      toast.current?.show({ severity: 'error', summary: 'Error', detail: e?.response?.data?.detail || 'Save failed', life: 5000 });
    }
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
          onChange={(e) => handleFormatChange(e.value)}
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
                        <ChromatographicSnip
                          ref={(el) => { snipRefs.current[stage.format_stage_mapping_id] = el; }}
                          questions={stage.questions}
                          stageName={stage.stage_name}
                          stageStatus={stage.status}
                        />
                      )}
                      {/* Approval section — not Basic Details */}
                      {stage.stage_name !== 'Basic Details' && (
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
