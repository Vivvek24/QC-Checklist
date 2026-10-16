/**
 * QuestionApprovalLabels — the per-question approval sign-off block rendered
 * under an approvable question in the Create Request grid.
 *
 * Mirrors the stage approval remark flow (ApprovalSnip) but per question: each
 * configured approval label is either a remark dropdown (only the first
 * un-acted label is editable at a time), or — once acted — a read-only line
 * showing the recorded remark, who acted, and when.
 *
 * Pure presentational: all state lives in useQuestionApprovals and is passed
 * in via the QuestionApprovalAccess object.
 */

import { Dropdown } from 'primereact/dropdown';
import { InputTextarea } from 'primereact/inputtextarea';
import { useActedDateFormatter } from '../hooks/useActedDateFormatter';
import type { QuestionAnswerPreview } from '../models/TemplateTypes';

/** Prior-acted info for a question+label approval (read-only display). */
export interface ApprovalActedInfo {
  remark_id: number | null;
  remark: string;
  user_id: number | null;
  date_of_action: string | null;
}

/** Access to the per-question approval remark state (mirrors stage remarks). */
export interface QuestionApprovalAccess {
  canAct: boolean;
  remarkOptions: { label: string; value: number; isOthers: boolean }[];
  remarkLabelById: Map<number, string>;
  /** Resolve an acting user's id to a display name (same as the stage snip). */
  userNameById?: (userId: number) => string;
  getPick: (sqmId: number, labelId: number) => number | null | undefined;
  getPickText: (sqmId: number, labelId: number) => string;
  setPick: (sqmId: number, labelId: number, remarkId: number | null) => void;
  setPickText: (sqmId: number, labelId: number, text: string) => void;
  getActed: (sqmId: number, labelId: number) => ApprovalActedInfo | undefined;
  isActed: (sqmId: number, labelId: number) => boolean;
  /** The one editable label for a question (first un-acted, in config order). */
  getEditableLabelId: (sqmId: number, orderedLabelIds: number[]) => number | null;
  /** Inline validation error for a question+label's remark, if any. */
  getError: (sqmId: number, labelId: number) => string | undefined;
}

const OTHERS = 'Others';

/** One approval label under a question: a remark dropdown (fillable), the
 * recorded remark (read-only once acted), or a "Pending" line (not yet its turn). */
const QuestionApprovalLabel = ({
  sqmId, labelId, labelText, isEditable, access, formatDate,
}: {
  sqmId: number;
  labelId: number;
  labelText: string;
  /** True only for the single label the current user may act on now (first
   * un-acted in config order) — mirrors the stage approval editable label. */
  isEditable: boolean;
  access: QuestionApprovalAccess;
  formatDate: (iso: string | null) => string;
}) => {
  const acted = access.getActed(sqmId, labelId);

  // Already acted — show the recorded remark + who acted + when (read-only).
  if (acted) {
    const text = acted.remark_id != null
      ? (access.remarkLabelById.get(acted.remark_id) === OTHERS ? (acted.remark || OTHERS) : access.remarkLabelById.get(acted.remark_id) ?? acted.remark)
      : acted.remark;
    const actedByName = acted.user_id != null && access.userNameById ? access.userNameById(acted.user_id) : '';
    const actedDate = formatDate(acted.date_of_action);
    return (
      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.1rem', fontSize: '0.72rem', color: '#334155', minWidth: '10rem' }}>
        <span style={{ fontWeight: 600, color: '#475569' }}>{labelText}</span>
        <span><i className="pi pi-check-circle" style={{ color: '#16a34a', fontSize: '0.7rem', marginRight: '0.25rem' }} />{text || '—'}</span>
        {actedByName && <span style={{ color: '#475569', fontWeight: 600 }}>{actedByName}</span>}
        {actedDate && <span style={{ color: '#94a3b8' }}>{actedDate}</span>}
      </div>
    );
  }

  // Not this user's turn for this label (a prior label is still un-acted, or
  // the stage isn't actionable) — show a plain pending line.
  if (!isEditable) {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.2rem', fontSize: '0.72rem', color: '#475569', minWidth: '10rem' }}>
        <span style={{ fontWeight: 600 }}>{labelText}</span>
        <span style={{ color: '#94a3b8', fontStyle: 'italic' }}>Pending</span>
      </div>
    );
  }

  const selected = access.getPick(sqmId, labelId) ?? null;
  const isOthers = access.remarkOptions.find((o) => o.value === selected)?.isOthers ?? false;
  const err = access.getError(sqmId, labelId);
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem', minWidth: '12rem' }}>
      <span style={{ fontWeight: 600, fontSize: '0.72rem', color: '#475569' }}>{labelText}</span>
      <Dropdown
        value={selected}
        onChange={(e) => {
          access.setPick(sqmId, labelId, e.value);
          const picked = access.remarkOptions.find((o) => o.value === e.value);
          if (!picked?.isOthers) access.setPickText(sqmId, labelId, '');
        }}
        options={access.remarkOptions}
        placeholder="Select Remark"
        filter
        showClear
        className={err ? 'p-invalid' : ''}
        style={{ height: '1.9rem', fontSize: '0.72rem', width: '100%' }}
      />
      {isOthers && (
        <InputTextarea
          value={access.getPickText(sqmId, labelId)}
          onChange={(e) => access.setPickText(sqmId, labelId, e.target.value)}
          placeholder="Enter remark..."
          rows={2}
          className={err ? 'p-invalid' : ''}
          style={{ width: '100%', fontSize: '0.72rem' }}
        />
      )}
      {err && <small className="qc-validation-error">{err}</small>}
    </div>
  );
};

interface QuestionApprovalLabelsProps {
  row: QuestionAnswerPreview;
  access?: QuestionApprovalAccess;
}

/** The whole approval sign-off block for one question (nothing when the
 * question isn't approvable or has no labels). */
export const QuestionApprovalLabels = ({ row, access }: QuestionApprovalLabelsProps) => {
  const formatDate = useActedDateFormatter();
  if (!access || !row.is_approvable || (row.approval_labels?.length ?? 0) === 0) return null;

  const sqmId = row.stage_question_mapping_id;
  const orderedLabelIds = row.approval_labels!.map((al) => al.approval_label_id);
  const editableLabelId = access.getEditableLabelId(sqmId, orderedLabelIds);

  return (
    <div style={{ marginTop: '0.5rem', paddingTop: '0.4rem', borderTop: '1px dashed #e2e8f0', display: 'flex', flexWrap: 'wrap', gap: '0.75rem 1.25rem' }}>
      {row.approval_labels!.map((al) => (
        <QuestionApprovalLabel
          key={al.approval_label_id}
          sqmId={sqmId}
          labelId={al.approval_label_id}
          labelText={al.label}
          isEditable={al.approval_label_id === editableLabelId}
          access={access}
          formatDate={formatDate}
        />
      ))}
    </div>
  );
};
