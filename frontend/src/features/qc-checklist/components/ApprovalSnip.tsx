/**
 * ApprovalSnip — grid component for declaration questions in approval stages.
 * Also shows approval labels (side by side) and a remark dropdown.
 *
 * Exposes a ref handle so the submit flow can read + validate the remark:
 *  - getRemark()      → { remark_id, remark_text } for the submit payload
 *  - validateRemark() → true when a remark is chosen (and free-text filled
 *    when "Others" is selected); surfaces an inline error otherwise.
 */

import { forwardRef, useEffect, useImperativeHandle, useState } from 'react';
import { Dropdown } from 'primereact/dropdown';
import { InputTextarea } from 'primereact/inputtextarea';
import { MultiSelect } from 'primereact/multiselect';
import { InputText } from 'primereact/inputtext';
import { useRemarks } from '../../masters/hooks/useRemarks';
import type { SubmitStageAnswerInput } from '../api/qcChecklistApi';
import type { SavedAnswer } from '../hooks/useValidateTemplateAnswers';

const OTHERS_REMARK = 'Others';

interface QuestionAnswerPreview {
  stage_question_mapping_id: number;
  question_id: number;
  question_title: string;
  serial_number: number;
  answer_type: string;
  has_text_box: boolean;
  is_declaration_question: boolean;
  options: { id: number; label: string }[];
  response_options: { id: number; label: string }[];
}

interface ApprovalLabelPreview {
  approval_label_id: number;
  label: string;
}

/** A persisted approval-label mapping (who acted on a label, with remark + date). */
export interface ApprovalLabelMapping {
  approval_label_id: number;
  remark_id: number | null;
  user_id: number | null;
  date_of_action: string | null;
  remark: string;
  is_refer_back: boolean;
}

interface Props {
  questions: QuestionAnswerPreview[];
  approvalLabels: ApprovalLabelPreview[];
  hasDeclarationQuestion: boolean;
  /** Persisted mappings for this stage's labels — drives read-only vs pending. */
  mappings?: ApprovalLabelMapping[];
  /** True when the current user can act on this stage (fillable). When false,
   * the remark dropdown is hidden and everything is read-only. */
  canAct?: boolean;
  /** The stage's live status — drives refer-back re-editing of the remark. */
  stageStatus?: string;
  /** Resolves an acting user's id to a display name (resolved on the UI). */
  userNameById?: (userId: number) => string;
  /** True only while the stage is fillable by the analyst — declaration answers
   * are editable only then; the approver sees them read-only. */
  canFillDeclarations?: boolean;
  /** Pre-loaded saved declaration answers (keyed by stage_question_mapping_id).
   * Declaration answers are persisted on submit and shown read-only afterward
   * (so the approver can't edit them). */
  savedAnswers?: Record<number, SavedAnswer>;
}

export interface ApprovalSnipHandle {
  /** The chosen remark for the submit payload. */
  getRemark: () => { remark_id: number | null; remark_text: string };
  /** True when a valid remark is selected; sets an inline error otherwise. */
  validateRemark: () => boolean;
  /** True when every answerable declaration question has a value; sets inline
   * errors otherwise. */
  validateDeclarations: () => boolean;
  /** The declaration answers for the submit payload (one per answerable
   * declaration question the user filled). */
  getDeclarationAnswers: () => SubmitStageAnswerInput[];
}

export const ApprovalSnip = forwardRef<ApprovalSnipHandle, Props>(
  ({ questions, approvalLabels, hasDeclarationQuestion, mappings = [], canAct = true, stageStatus, userNameById, canFillDeclarations = false, savedAnswers }, ref) => {
  const declarationQuestions = questions.filter((q) => q.is_declaration_question);
  // Declaration answers are editable only while the stage is fillable by the
  // analyst; once submitted they're read-only (the approver can't edit).
  const declarationsLocked = !canFillDeclarations;
  const { data: remarksData } = useRemarks();
  const remarkOptions = (remarksData?.items ?? []).map(
    (r: { id: string | number; remark: string }) => ({ label: r.remark, value: Number(r.id), isOthers: r.remark === OTHERS_REMARK })
  );
  const remarkLabelById = new Map<number, string>(
    (remarksData?.items ?? []).map((r: { id: string | number; remark: string }) => [Number(r.id), r.remark])
  );

  // Map each approval label to its persisted mapping (if any).
  const mappingByLabel = new Map<number, ApprovalLabelMapping>(
    mappings.map((m) => [m.approval_label_id, m])
  );
  const hasActed = (labelId: number) => {
    const m = mappingByLabel.get(labelId);
    return !!(m && m.date_of_action);
  };

  const isReferBack = stageStatus === 'ReferBack';

  // Which label the current user edits:
  //  - On refer-back: the initiator re-edits their OWN label — the one that was
  //    acted on but is NOT the refer-back action itself. Its prior remark is
  //    pre-filled so the initiator can revise it.
  //  - Otherwise: the first label that hasn't been acted on yet.
  const editableLabelId: number | null = (() => {
    if (!canAct) return null;
    if (isReferBack) {
      const own = approvalLabels.find((al) => {
        const m = mappingByLabel.get(al.approval_label_id);
        return m && m.date_of_action && !m.is_refer_back;
      });
      if (own) return own.approval_label_id;
    }
    return approvalLabels.find((al) => !hasActed(al.approval_label_id))?.approval_label_id ?? null;
  })();

  // A label renders read-only when it's been acted on AND isn't the one the
  // current user is (re-)editing.
  const isActed = (labelId: number) => hasActed(labelId) && labelId !== editableLabelId;

  /** Render the saved remark for an acted label. */
  const actedRemarkText = (labelId: number): string => {
    const m = mappingByLabel.get(labelId);
    if (!m) return '';
    if (m.remark_id != null && remarkLabelById.get(m.remark_id) === OTHERS_REMARK) return m.remark || OTHERS_REMARK;
    if (m.remark_id != null) return remarkLabelById.get(m.remark_id) ?? m.remark;
    return m.remark;
  };
  const actedDate = (labelId: number): string => {
    const d = mappingByLabel.get(labelId)?.date_of_action;
    if (!d) return '';
    const dt = new Date(d);
    const dd = String(dt.getDate()).padStart(2, '0');
    const mm = String(dt.getMonth() + 1).padStart(2, '0');
    const yyyy = dt.getFullYear();
    return `${dd}-${mm}-${yyyy}`;
  };
  /** Display name of the user who acted on a label (resolved on the UI). */
  const actedByName = (labelId: number): string => {
    const uid = mappingByLabel.get(labelId)?.user_id;
    return uid != null && userNameById ? userNameById(uid) : '';
  };

  const [answers, setAnswers] = useState<Record<number, any>>({});
  const [answerErrors, setAnswerErrors] = useState<Record<number, string>>({});

  // Seed declaration answers from the saved values (resuming / approver view),
  // so they render pre-filled and read-only once submitted.
  useEffect(() => {
    if (!savedAnswers) return;
    const typeByKey = new Map<number, string>(
      declarationQuestions.map((q) => [q.stage_question_mapping_id, q.answer_type])
    );
    const next: Record<number, any> = {};
    for (const [k, sa] of Object.entries(savedAnswers)) {
      const key = Number(k);
      if (!typeByKey.has(key)) continue; // only declaration rows
      if (sa.question_option_id != null) {
        next[key] = typeByKey.get(key) === 'Dropdown (multi select)'
          ? [sa.question_option_id]
          : sa.question_option_id;
      } else if (sa.textbox_value) {
        next[key] = sa.textbox_value;
      }
    }
    setAnswers((prev) => ({ ...next, ...prev }));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [savedAnswers]);
  const [selectedRemarkId, setSelectedRemarkId] = useState<number | null>(null);
  const [remarkText, setRemarkText] = useState('');
  const [remarkError, setRemarkError] = useState<string | null>(null);

  // On refer-back, pre-fill the dropdown with the initiator's prior remark so
  // they can revise rather than re-pick from scratch.
  useEffect(() => {
    if (editableLabelId == null) return;
    const m = mappingByLabel.get(editableLabelId);
    if (m && m.date_of_action && m.remark_id != null) {
      setSelectedRemarkId(m.remark_id);
      setRemarkText(m.remark || '');
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [editableLabelId, mappings]);

  const isOthersSelected = remarkOptions.find((o) => o.value === selectedRemarkId)?.isOthers ?? false;

  useImperativeHandle(ref, () => ({
    getRemark: () => ({ remark_id: selectedRemarkId, remark_text: isOthersSelected ? remarkText.trim() : '' }),
    validateRemark: () => {
      if (selectedRemarkId == null) {
        setRemarkError('Please select a remark.');
        return false;
      }
      if (isOthersSelected && !remarkText.trim()) {
        setRemarkError('Please enter a remark.');
        return false;
      }
      setRemarkError(null);
      return true;
    },
    validateDeclarations: () => {
      // Only the filling analyst answers declaration questions; skip when not
      // fillable (e.g. an approver viewing — the answers are already saved).
      if (!canFillDeclarations) return true;
      const next: Record<number, string> = {};
      let ok = true;
      for (const row of declarationQuestions) {
        const key = row.stage_question_mapping_id;
        const isNone = row.answer_type === 'None' && !row.has_text_box;
        if (isNone) continue; // nothing to answer
        const value = answers[key];
        const empty =
          value == null ||
          (typeof value === 'string' && !value.trim()) ||
          (Array.isArray(value) && value.length === 0);
        if (empty) {
          next[key] = 'This field is required.';
          ok = false;
        }
      }
      setAnswerErrors(next);
      return ok;
    },
    getDeclarationAnswers: () => {
      const out: SubmitStageAnswerInput[] = [];
      for (const row of declarationQuestions) {
        const key = row.stage_question_mapping_id;
        const isNone = row.answer_type === 'None' && !row.has_text_box;
        if (isNone) continue;
        const value = answers[key];
        const isSelect = row.answer_type === 'Dropdown (single select)' || row.answer_type === 'Dropdown (multi select)';
        const optionId = isSelect
          ? (Array.isArray(value) ? (value[0] ?? null) : (typeof value === 'number' ? value : null))
          : null;
        const text = !isSelect && typeof value === 'string' ? value : '';
        // Skip rows the user didn't fill.
        if (optionId == null && !text) continue;
        out.push({
          stage_question_mapping_id: key,
          question_id: row.question_id,
          textbox_value: text,
          question_option_id: optionId,
          response_answer: '',
          helpers: [],
        });
      }
      return out;
    },
  }), [selectedRemarkId, remarkText, isOthersSelected, canFillDeclarations, declarationQuestions, answers]);

  return (
    <div style={{ paddingTop: '0.75rem' }}>
      {/* Approval Labels — each with its own state: acted labels show the
          recorded remark + date (read-only); the first pending label shows
          the remark dropdown for the current user to act on. */}
      {approvalLabels.length > 0 && (
        <div style={{ padding: '0.5rem 0.75rem', borderBottom: '1px solid #e2e8f0', background: '#f8fafc', display: 'flex', gap: '1rem' }}>
          {approvalLabels.map((al) => {
            const acted = isActed(al.approval_label_id);
            const isPendingForMe = canAct && al.approval_label_id === editableLabelId;
            return (
              <div key={al.approval_label_id} style={{ flex: 1, minWidth: 0 }}>
                <div style={{ fontSize: '0.78rem', fontWeight: 700, color: '#475569', marginBottom: '0.3rem' }}>
                  {al.label}
                </div>

                {acted ? (
                  /* Already acted — show recorded remark, who acted, and when. */
                  <div style={{ fontSize: '0.72rem', color: '#334155' }}>
                    <div><i className="pi pi-check-circle" style={{ color: '#16a34a', fontSize: '0.72rem', marginRight: '0.3rem' }} />
                      {actedRemarkText(al.approval_label_id) || '—'}</div>
                    {actedByName(al.approval_label_id) && (
                      <div style={{ color: '#475569', marginTop: '0.15rem', fontWeight: 600 }}>
                        {actedByName(al.approval_label_id)}
                      </div>
                    )}
                    {actedDate(al.approval_label_id) && (
                      <div style={{ color: '#94a3b8', marginTop: '0.1rem' }}>{actedDate(al.approval_label_id)}</div>
                    )}
                  </div>
                ) : isPendingForMe ? (
                  /* The label the current user acts on — remark dropdown. */
                  <>
                    <Dropdown
                      value={selectedRemarkId}
                      onChange={(e) => {
                        setSelectedRemarkId(e.value);
                        setRemarkError(null);
                        const picked = remarkOptions.find((o) => o.value === e.value);
                        if (!picked?.isOthers) setRemarkText('');
                      }}
                      placeholder="Select Remark"
                      style={{ height: '2rem', fontSize: '0.75rem', width: '100%' }}
                      className={remarkError ? 'p-invalid' : ''}
                      options={remarkOptions}
                      filter
                      showClear
                    />
                    {isOthersSelected && (
                      <InputTextarea
                        value={remarkText}
                        onChange={(e) => { setRemarkText(e.target.value); setRemarkError(null); }}
                        placeholder="Enter remark..."
                        rows={2}
                        className={remarkError ? 'p-invalid' : ''}
                        style={{ width: '100%', fontSize: '0.75rem', marginTop: '0.4rem' }}
                      />
                    )}
                    {remarkError && (
                      <small className="qc-validation-error" style={{ display: 'block', marginTop: '0.25rem' }}>
                        {remarkError}
                      </small>
                    )}
                  </>
                ) : (
                  /* Not yet reached (waiting for a prior approver). */
                  <div style={{ fontSize: '0.72rem', color: '#94a3b8', fontStyle: 'italic' }}>Pending</div>
                )}
              </div>
            );
          })}
        </div>
      )}

      {/* Declaration Questions grid */}
      {hasDeclarationQuestion && declarationQuestions.length > 0 && (
        <>
          <div style={{ padding: '0.4rem 0.75rem', fontWeight: 700, fontSize: '0.8rem', color: '#475569', borderBottom: '1px solid #e2e8f0', background: '#f8fafc' }}>
            Declaration Questions
          </div>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.78rem' }}>
            <thead>
              <tr style={{ background: '#f8fafc' }}>
                <th style={{ padding: '0.5rem 0.75rem', textAlign: 'left', fontWeight: 700, color: '#475569', borderBottom: '1px solid #e2e8f0' }}>Question</th>
                <th style={{ padding: '0.5rem 0.75rem', textAlign: 'left', fontWeight: 700, color: '#475569', width: '18rem', borderBottom: '1px solid #e2e8f0' }}>Response Answer</th>
              </tr>
            </thead>
            <tbody>
              {declarationQuestions.map((row) => {
                const key = row.stage_question_mapping_id;
                const showTextBox = row.answer_type === 'Text Box' || row.has_text_box;
                const isMultiSelect = row.answer_type === 'Dropdown (multi select)';
                const isSingleSelect = row.answer_type === 'Dropdown (single select)';
                const isNone = row.answer_type === 'None' && !row.has_text_box;

                // Single/multi-select declaration questions populate from the
                // question's own options (not its response options).
                const selectOpts = (row.options || []).map((o) => ({ label: o.label, value: o.id }));

                return (
                  <tr key={key} style={{ borderBottom: '1px solid #f1f5f9' }}>
                    <td style={{ padding: '0.5rem 0.75rem', color: '#1e293b' }}>{row.question_title}</td>
                    <td style={{ padding: '0.5rem 0.75rem' }}>
                      {(() => {
                        const err = answerErrors[key];
                        const onChangeClear = (value: any) => {
                          setAnswers((p) => ({ ...p, [key]: value }));
                          setAnswerErrors((p) => { if (!p[key]) return p; const n = { ...p }; delete n[key]; return n; });
                        };
                        if (isNone) {
                          return <span style={{ color: '#94a3b8', fontSize: '0.78rem' }}>N/A</span>;
                        }
                        // Read-only once submitted (approver view): show the saved value.
                        if (declarationsLocked) {
                          const v = answers[key];
                          const text = isMultiSelect
                            ? (Array.isArray(v) ? v : []).map((id) => selectOpts.find((o) => o.value === id)?.label ?? id).join(', ')
                            : isSingleSelect
                              ? (selectOpts.find((o) => o.value === v)?.label ?? '')
                              : (typeof v === 'string' ? v : '');
                          return <span style={{ color: '#334155', fontSize: '0.78rem' }}>{text || '—'}</span>;
                        }
                        const control = isMultiSelect ? (
                          <MultiSelect
                            value={answers[key] || []}
                            options={selectOpts}
                            onChange={(e) => onChangeClear(e.value)}
                            filter
                            display="chip"
                            className={err ? 'w-full p-invalid' : 'w-full'}
                            style={{ minHeight: '1.85rem', fontSize: '0.75rem' }}
                          />
                        ) : isSingleSelect ? (
                          <Dropdown
                            value={answers[key] || null}
                            options={selectOpts}
                            onChange={(e) => onChangeClear(e.value)}
                            filter
                            showClear
                            className={err ? 'w-full p-invalid' : 'w-full'}
                            style={{ height: '1.85rem', fontSize: '0.75rem' }}
                          />
                        ) : showTextBox ? (
                          <InputText
                            value={answers[key] || ''}
                            onChange={(e) => onChangeClear(e.target.value)}
                            className={err ? 'w-full p-invalid' : 'w-full'}
                            style={{ height: '1.85rem', fontSize: '0.75rem' }}
                          />
                        ) : (
                          <span style={{ color: '#94a3b8', fontSize: '0.78rem' }}>N/A</span>
                        );
                        return (
                          <div className="flex flex-column gap-1">
                            {control}
                            {err && <small className="qc-validation-error">{err}</small>}
                          </div>
                        );
                      })()}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </>
      )}
    </div>
  );
});

ApprovalSnip.displayName = 'ApprovalSnip';

