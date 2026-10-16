/**
 * TemplateCell — renders a single cell of TemplateDrivenSnip's grid, branching
 * on the column's column_type. Pure presentational: all state lives in the
 * caller (useValidateTemplateAnswers) and is passed in / mutated via callbacks.
 */

import { InputText } from 'primereact/inputtext';
import { RadioButton } from 'primereact/radiobutton';
import { OptionSelector } from './OptionSelector';
import { QuestionApprovalLabels, type QuestionApprovalAccess } from './QuestionApprovalLabels';
import type { ColumnPreview } from '../models/ChecklistPreview';
import type { QuestionAnswerPreview } from '../models/TemplateTypes';
import type { RowErrors } from '../hooks/useValidateTemplateAnswers';

// Re-export so existing importers (TemplateDrivenSnip) keep their import path.
export type { QuestionApprovalAccess, ApprovalActedInfo } from './QuestionApprovalLabels';

type ColumnLike = Pick<ColumnPreview, 'column_type'>;

/** Access to one sub-question's answer state (keyed in the hook by parent sqm
 * id + sub question id). The cell passes the parent row + sub question id. */
export interface SubAnswerAccess {
  getSelection: (parentSqmId: number, subQuestionId: number) => unknown;
  getAnswer: (parentSqmId: number, subQuestionId: number) => string;
  getResponse: (parentSqmId: number, subQuestionId: number) => string;
  setSelection: (parentSqmId: number, subQuestionId: number, value: unknown) => void;
  setAnswer: (parentSqmId: number, subQuestionId: number, value: string) => void;
  setResponse: (parentSqmId: number, subQuestionId: number, value: string) => void;
}

interface Props {
  column: ColumnLike;
  row: QuestionAnswerPreview;
  canAdd: boolean;
  /** True when the stage is read-only (Pending/Approved) — disables all inputs. */
  disabled?: boolean;
  rowErr?: RowErrors;
  selection: unknown;
  onSelectionChange: (value: unknown) => void;
  answer: string;
  onAnswerChange: (value: string) => void;
  response: string;
  onResponseChange: (value: string) => void;
  helperValues: string[];
  /** Per-helper-index inline error messages (undefined = no error). */
  helperErrors?: (string | undefined)[];
  onHelperChange: (idx: number, value: string) => void;
  onHelperRemove: (idx: number) => void;
  onHelperAdd: () => void;
  /** Sub-question answer state access (used only by the QUESTION cell). */
  subAccess?: SubAnswerAccess;
  /** Per-question approval remark access (used only by the QUESTION cell). */
  approvalAccess?: QuestionApprovalAccess;
  /** True when this row is the SAP-lookup trigger (the editable INSP_LOT
   * question in Basic Details). On blur of its answer box, the entered value
   * is used to look up SAP and auto-fill the other mapped answers. */
  isSapTrigger?: boolean;
  sapLoading?: boolean;
  sapError?: string | null;
  onSapFetch?: () => void;
}

/** Renders one sub-question's input under its parent, matching its answer_type. */
const SubQuestionInput = ({
  parent, sub, access, locked,
}: {
  parent: QuestionAnswerPreview;
  sub: QuestionAnswerPreview;
  access: SubAnswerAccess;
  locked: boolean;
}) => {
  const pid = parent.stage_question_mapping_id;
  const sid = sub.question_id;
  const isOption = sub.answer_type === 'Dropdown (single select)' || sub.answer_type === 'Dropdown (multi select)';
  const showTextBox = sub.answer_type === 'Text Box' || (sub.answer_type !== 'None' && sub.has_text_box);

  // Just the input — the sub-question's title is shown in the QUESTION column,
  // row-aligned with this input in the Enter Answer column.
  if (isOption) {
    return (
      <OptionSelector
        answerType={sub.answer_type}
        options={sub.options}
        value={access.getSelection(pid, sid)}
        onChange={(val) => access.setSelection(pid, sid, val)}
        disabled={locked}
      />
    );
  }
  if (showTextBox) {
    return (
      <InputText
        value={access.getAnswer(pid, sid)}
        className="w-full"
        onChange={(e) => access.setAnswer(pid, sid, e.target.value)}
        disabled={locked}
        style={{ height: '1.85rem', fontSize: '0.75rem' }}
      />
    );
  }
  return (
    <div className="flex align-items-center gap-3">
      {['YES', 'NO', 'N/A'].map((v) => (
        <div key={v} className="flex align-items-center gap-1">
          <RadioButton
            name={`subresp_${pid}_${sid}`}
            value={v}
            checked={access.getResponse(pid, sid) === v}
            onChange={() => access.setResponse(pid, sid, v)}
            disabled={locked}
          />
          <label style={{ fontSize: '0.72rem' }}>{v}</label>
        </div>
      ))}
    </div>
  );
};

export const TemplateCell = ({
  column,
  row,
  canAdd,
  disabled = false,
  rowErr,
  selection,
  onSelectionChange,
  answer,
  onAnswerChange,
  response,
  onResponseChange,
  helperValues,
  helperErrors,
  onHelperChange,
  onHelperRemove,
  onHelperAdd,
  subAccess,
  approvalAccess,
  isSapTrigger = false,
  sapLoading = false,
  sapError = null,
  onSapFetch,
}: Props) => {
  const key = row.stage_question_mapping_id;
  // Locked either because the whole stage is read-only, or because this
  // question is configured non-editable (is_editable=false) in Template Studio.
  const locked = disabled || row.is_editable === false;

  switch (column.column_type) {
    case 'SERIAL':
      return <span style={{ fontWeight: 500 }}>{row.serial_number}</span>;

    case 'QUESTION':
      return (
        <div style={{ color: '#1e293b' }}>
          <div>{row.question_title}</div>
          {/* Sub-question titles listed here; their inputs are row-aligned in
              the Enter Answer column. */}
          {row.has_sub_question && (row.sub_questions?.length ?? 0) > 0 && (
            <div style={{ marginTop: '0.4rem', paddingLeft: '0.75rem', display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
              {row.sub_questions!.map((sub) => (
                <div
                  key={sub.question_id}
                  style={{ fontSize: '0.72rem', color: '#64748b', minHeight: '1.85rem', display: 'flex', alignItems: 'center' }}
                >
                  • {sub.question_title}
                </div>
              ))}
            </div>
          )}
          {/* Per-question approval sign-off block (remark dropdown while
              fillable; recorded remark + who + when once acted). */}
          <QuestionApprovalLabels row={row} access={approvalAccess} />
        </div>
      );

    case 'OPTION':
      return (
        <>
          <OptionSelector
            answerType={row.answer_type}
            options={row.options}
            value={selection}
            onChange={onSelectionChange}
            disabled={locked}
          />
          {rowErr?.options && <small className="qc-validation-error">{rowErr.options}</small>}
        </>
      );

    case 'AQL_LIMIT':
      return <span style={{ color: '#475569', fontWeight: 500 }}>{row.aql_limit ? parseFloat(row.aql_limit).toString() : '-'}</span>;

    case 'RESPONSE':
      return (
        <div className="flex flex-column">
          <div className="flex align-items-center gap-3">
            {['YES', 'NO', 'N/A'].map((v) => (
              <div key={v} className="flex align-items-center gap-1">
                <RadioButton
                  name={`response_${key}`}
                  value={v}
                  checked={response === v}
                  onChange={() => onResponseChange(v)}
                  disabled={locked}
                />
                <label style={{ fontSize: '0.72rem' }}>{v}</label>
              </div>
            ))}
          </div>
          {rowErr?.response && <small className="qc-validation-error">{rowErr.response}</small>}
        </div>
      );

    case 'ANSWER':
    default: {
      const showNA = row.answer_type !== 'Text Box' && (row.answer_type === 'None' || !row.has_text_box);
      const hasSubInputs = subAccess && row.has_sub_question && (row.sub_questions?.length ?? 0) > 0;

      // The parent's own answer control (or N/A). Sub-question inputs (if any)
      // are appended below, each row-aligned with its title in the Question col.
      const parentAnswer = showNA
        ? <span style={{ color: '#94a3b8', fontSize: '0.78rem' }}>N/A</span>
        : null;

      if (showNA && hasSubInputs) {
        return (
          <div className="flex flex-column gap-1">
            {parentAnswer}
            <div style={{ marginTop: '0.4rem', display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
              {row.sub_questions!.map((sub) => (
                <SubQuestionInput key={sub.question_id} parent={row} sub={sub} access={subAccess!} locked={locked} />
              ))}
            </div>
          </div>
        );
      }
      if (showNA) return parentAnswer;

      return (
        <div className="flex flex-column gap-1">
          <div className="flex align-items-center gap-2">
            <InputText
              value={answer}
              className={rowErr?.answer ? 'w-full p-invalid' : 'w-full'}
              onChange={(e) => onAnswerChange(e.target.value)}
              // SAP trigger: look up on blur so we hit SAP once the value is
              // entered, not on every keystroke.
              onBlur={isSapTrigger && !locked ? onSapFetch : undefined}
              disabled={locked}
              style={{ height: '1.85rem', fontSize: '0.75rem' }}
            />
            {isSapTrigger && sapLoading && (
              <i className="pi pi-spin pi-spinner" style={{ fontSize: '0.8rem', color: 'var(--color-primary)' }} />
            )}
          </div>
          {rowErr?.answer && <small className="qc-validation-error">{rowErr.answer}</small>}
          {isSapTrigger && sapError && <small className="qc-validation-error">{sapError}</small>}
          {helperValues.map((val, idx) => {
            const helperErr = helperErrors?.[idx];
            return (
              <div key={idx} className="flex flex-column gap-1">
                <div className="flex align-items-center gap-1">
                  <InputText
                    value={val}
                    className={helperErr ? 'flex-1 p-invalid' : 'flex-1'}
                    onChange={(e) => onHelperChange(idx, e.target.value)}
                    disabled={locked}
                    style={{ height: '1.85rem', fontSize: '0.75rem' }}
                  />
                  {!locked && (
                    <button
                      type="button"
                      onClick={() => onHelperRemove(idx)}
                      style={{
                        border: 'none', background: 'transparent', color: 'var(--color-error)',
                        cursor: 'pointer', fontSize: '0.85rem', padding: '0 0.25rem',
                      }}
                    >
                      <i className="pi pi-times" style={{ fontSize: '0.7rem' }} />
                    </button>
                  )}
                </div>
                {helperErr && <small className="qc-validation-error">{helperErr}</small>}
              </div>
            );
          })}
          {row.has_multiple_text_box && canAdd && !locked && (
            <button
              type="button"
              onClick={onHelperAdd}
              style={{
                border: '1px solid var(--color-primary)', borderRadius: '4px',
                background: 'transparent', color: 'var(--color-primary)',
                fontSize: '0.7rem', padding: '0.2rem 0.5rem', cursor: 'pointer',
                width: 'fit-content',
              }}
            >
              + Add
            </button>
          )}
          {/* Sub-question inputs, row-aligned with their titles in the Question
              column. */}
          {hasSubInputs && (
            <div style={{ marginTop: '0.4rem', display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
              {row.sub_questions!.map((sub) => (
                <SubQuestionInput key={sub.question_id} parent={row} sub={sub} access={subAccess!} locked={locked} />
              ))}
            </div>
          )}
        </div>
      );
    }
  }
};
