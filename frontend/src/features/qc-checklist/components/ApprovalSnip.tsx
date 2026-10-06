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

const OTHERS_REMARK = 'Others';

interface QuestionAnswerPreview {
  stage_question_mapping_id: number;
  question_id: number;
  question_title: string;
  serial_number: number;
  answer_type: string;
  has_text_box: boolean;
  is_declaration_question: boolean;
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
}

export interface ApprovalSnipHandle {
  /** The chosen remark for the submit payload. */
  getRemark: () => { remark_id: number | null; remark_text: string };
  /** True when a valid remark is selected; sets an inline error otherwise. */
  validateRemark: () => boolean;
}

export const ApprovalSnip = forwardRef<ApprovalSnipHandle, Props>(
  ({ questions, approvalLabels, hasDeclarationQuestion, mappings = [], canAct = true, stageStatus, userNameById }, ref) => {
  const declarationQuestions = questions.filter((q) => q.is_declaration_question);
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
  }), [selectedRemarkId, remarkText, isOthersSelected]);

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

                const responseOpts = (row.response_options || []).map((o) => ({ label: o.label, value: o.id }));

                return (
                  <tr key={key} style={{ borderBottom: '1px solid #f1f5f9' }}>
                    <td style={{ padding: '0.5rem 0.75rem', color: '#1e293b' }}>{row.question_title}</td>
                    <td style={{ padding: '0.5rem 0.75rem' }}>
                      {isNone ? (
                        <span style={{ color: '#94a3b8', fontSize: '0.78rem' }}>N/A</span>
                      ) : isMultiSelect ? (
                        <MultiSelect
                          value={answers[key] || []}
                          options={responseOpts}
                          onChange={(e) => setAnswers((p) => ({ ...p, [key]: e.value }))}
                          placeholder="Select"
                          filter
                          display="chip"
                          className="w-full"
                          style={{ minHeight: '1.85rem', fontSize: '0.75rem' }}
                        />
                      ) : isSingleSelect ? (
                        <Dropdown
                          value={answers[key] || null}
                          options={responseOpts}
                          onChange={(e) => setAnswers((p) => ({ ...p, [key]: e.value }))}
                          placeholder="Select"
                          filter
                          showClear
                          className="w-full"
                          style={{ height: '1.85rem', fontSize: '0.75rem' }}
                        />
                      ) : showTextBox ? (
                        <InputText
                          value={answers[key] || ''}
                          onChange={(e) => setAnswers((p) => ({ ...p, [key]: e.target.value }))}
                          className="w-full"
                          style={{ height: '1.85rem', fontSize: '0.75rem' }}
                        />
                      ) : (
                        <span style={{ color: '#94a3b8', fontSize: '0.78rem' }}>N/A</span>
                      )}
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

