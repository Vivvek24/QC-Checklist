/**
 * TemplateCell — renders a single cell of TemplateDrivenSnip's grid, branching
 * on the column's column_type. Pure presentational: all state lives in the
 * caller (useValidateTemplateAnswers) and is passed in / mutated via callbacks.
 */

import { InputTextarea } from 'primereact/inputtextarea';
import { Dropdown, type DropdownChangeEvent } from 'primereact/dropdown';
import { Calendar } from 'primereact/calendar';
import { RadioButton } from 'primereact/radiobutton';
import { Button } from 'primereact/button';
import { OptionSelector } from './OptionSelector';
import { QuestionApprovalLabels, type QuestionApprovalAccess } from './QuestionApprovalLabels';
import type { ColumnPreview } from '../models/ChecklistPreview';
import type { QuestionAnswerPreview } from '../models/TemplateTypes';
import type { RowErrors } from '../hooks/useValidateTemplateAnswers';

// Re-export so existing importers (TemplateDrivenSnip) keep their import path.
export type { QuestionApprovalAccess, ApprovalActedInfo } from './QuestionApprovalLabels';

/** Format a Date as dd-mm-yyyy hh:mm (24h) for read-only display, matching the
 * Date & Time picker's format. Empty when no value. */
const formatDateTime = (d: Date | null): string => {
  if (!d) return '—';
  const pad = (n: number) => String(n).padStart(2, '0');
  return `${pad(d.getDate())}-${pad(d.getMonth() + 1)}-${d.getFullYear()} ${pad(d.getHours())}:${pad(d.getMinutes())}`;
};

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
  /** Selected response-option id (RESPONSE_QUESTION_OPTION column). */
  responseOption?: number | null;
  onResponseOptionChange?: (value: number | null) => void;
  /** Product master options + selection for a "Masters" question's OPTION cell. */
  productOptions?: { label: string; value: number }[];
  productValue?: number | null;
  onProductChange?: (value: number | null) => void;
  /** Picked date-time for a "Date & Time" question's ANSWER cell. */
  dateValue?: Date | null;
  onDateChange?: (value: Date | null) => void;
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
  /** True when the user holds the Issue Vials permission — gates the button. */
  canIssueVials?: boolean;
  /** Opens the Issue Vials dialog for this row. */
  onIssueVials?: () => void;
  /** Running total (answer_total_vails) for a calculated question. */
  answerTotalVails?: number;
  /** "+ Add" action for a calculated question (validate + fold into a helper). */
  onCalculatedAdd?: () => void;
  /** Remove a calculated question's helper at idx (subtracts from the total). */
  onCalculatedRemove?: (idx: number) => void;
  /** Live-validate a calculated question's typed value (same rules as Add). */
  onCalculatedChange?: (value: string) => void;
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
      <InputTextarea
        value={access.getAnswer(pid, sid)}
        className="qc-grid-input w-full"
        onChange={(e) => access.setAnswer(pid, sid, e.target.value)}
        disabled={locked}
        rows={1}
        autoResize
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
  responseOption = null,
  onResponseOptionChange,
  productOptions = [],
  productValue = null,
  onProductChange,
  dateValue = null,
  onDateChange,
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
  canIssueVials = false,
  onIssueVials,
  answerTotalVails = 0,
  onCalculatedAdd,
  onCalculatedRemove,
  onCalculatedChange,
}: Props) => {
  const key = row.stage_question_mapping_id;
  // Locked when: the whole stage is read-only, the question is configured
  // non-editable (is_editable=false), OR it has a custom answer type — those
  // are system-calculated/auto-filled (e.g. Calculate_SampleConsumed), so the
  // user must not edit them.
  const hasCustomAnswer = !!row.custom_answers;
  const locked = disabled || row.is_editable === false || hasCustomAnswer;

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
      // A "Masters" question (e.g. Product Master) shows a dropdown of the
      // associated master's values instead of the question's own options.
      if (row.answer_type === 'Masters') {
        return (
          <>
            <Dropdown
              value={productValue}
              options={productOptions}
              onChange={(e: DropdownChangeEvent) => onProductChange?.(e.value ?? null)}
              placeholder="Select"
              filter
              showClear
              disabled={locked}
              className={`qc-grid-dropdown w-full${rowErr?.product ? ' p-invalid' : ''}`}
            />
            {rowErr?.product && <small className="qc-validation-error">{rowErr.product}</small>}
          </>
        );
      }
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

    case 'TEST_TITLE':
      // Read-only test name. Populated for auto-generated per-test rows; blank
      // for normal configured questions (which carry no test_title).
      return <span style={{ color: '#1e293b' }}>{row.test_title ?? ''}</span>;

    case 'SAMPLE_VIAL':
      // Read-only sample description for auto-generated per-test rows.
      return <span style={{ color: '#1e293b' }}>{row.sample_vails ?? ''}</span>;

    case 'ISSUE_VAILS':
      // An "Issue Vials" action button for the row — permission-gated. This is
      // an action trigger, not an answer input, so the answer-field `locked`
      // state (custom_answers / is_editable=false) must NOT disable it —
      // otherwise the button is un-clickable on exactly the rows that need it.
      if (!canIssueVials) return null;
      return (
        <Button
          label="Issue Vials"
          icon="pi pi-send"
          size="small"
          outlined
          type="button"
          onClick={onIssueVials}
          style={{ fontSize: '0.7rem', padding: '0.3rem 0.6rem' }}
        />
      );

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

    case 'RESPONSE_QUESTION_OPTION': {
      const respOpts = (row.response_options ?? []).map((o) => ({ label: o.label, value: o.id }));
      if (respOpts.length === 0) {
        return <span style={{ color: '#94a3b8', fontSize: '0.78rem' }}>N/A</span>;
      }
      return (
        <div className="flex flex-column">
          <Dropdown
            value={responseOption}
            options={respOpts}
            onChange={(e: DropdownChangeEvent) => onResponseOptionChange?.(e.value ?? null)}
            filter
            showClear
            disabled={locked}
            className={`qc-grid-dropdown w-full${rowErr?.responseOption ? ' p-invalid' : ''}`}
          />
          {rowErr?.responseOption && <small className="qc-validation-error">{rowErr.responseOption}</small>}
        </div>
      );
    }

    case 'ANSWER':
    default: {
      // Date & Time question: a date-time picker in the Enter Answer column.
      if (row.answer_type === 'Date & Time') {
        // Locked (read-only / non-editable / custom-answer) rows show the value
        // as plain text — a disabled Calendar can still surface its panel, so
        // render text instead to guarantee no interaction.
        if (locked) {
          return <span style={{ color: '#334155', fontSize: '0.78rem' }}>{formatDateTime(dateValue)}</span>;
        }
        return (
          <div className="flex flex-column gap-1">
            <Calendar
              value={dateValue}
              onChange={(e) => onDateChange?.((e.value as Date) ?? null)}
              showTime
              hourFormat="24"
              dateFormat="dd-mm-yy"
              showIcon
              placeholder="dd-mm-yyyy hh:mm"
              className={`qc-grid-calendar w-full${rowErr?.date ? ' p-invalid' : ''}`}
              panelClassName="qc-grid-calendar-panel"
            />
            {rowErr?.date && <small className="qc-validation-error">{rowErr.date}</small>}
          </div>
        );
      }

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
          <div className="flex align-items-start gap-2">
            {/* Auto-resizing textarea: long values wrap and grow the field's
                HEIGHT (the column width stays fixed). */}
            <InputTextarea
              value={answer}
              className={`qc-grid-input w-full${rowErr?.answer ? ' p-invalid' : ''}`}
              onChange={(e) => {
                onAnswerChange(e.target.value);
                // Calculated questions validate the typed value live (same
                // rules as the "+ Add" button).
                if (row.is_calculated) onCalculatedChange?.(e.target.value);
              }}
              // SAP trigger: look up on blur so we hit SAP once the value is
              // entered, not on every keystroke.
              onBlur={isSapTrigger && !locked ? onSapFetch : undefined}
              disabled={locked}
              rows={1}
              autoResize
            />
            {isSapTrigger && sapLoading && (
              <i className="pi pi-spin pi-spinner qc-grid-spinner" />
            )}
          </div>
          {rowErr?.answer && <small className="qc-validation-error">{rowErr.answer}</small>}
          {isSapTrigger && sapError && <small className="qc-validation-error">{sapError}</small>}
          {/* Calculated question: show the running total (answer_total_vails)
              in the same Enter Answer column. */}
          {row.is_calculated && (
            <div style={{ fontSize: '0.72rem', color: '#475569', fontWeight: 600 }}>
              Total: {answerTotalVails}
            </div>
          )}
          {helperValues.map((val, idx) => {
            const helperErr = helperErrors?.[idx];
            return (
              <div key={idx} className="flex flex-column gap-1">
                <div className="flex align-items-start gap-1">
                  <InputTextarea
                    value={val}
                    className={`qc-grid-input flex-1${helperErr ? ' p-invalid' : ''}`}
                    onChange={(e) => onHelperChange(idx, e.target.value)}
                    // Calculated helpers are system-generated — read-only (the
                    // value came from the validated "+ Add" flow).
                    disabled={locked || row.is_calculated}
                    rows={1}
                    autoResize
                  />
                  {!locked && canAdd && (
                    <button
                      type="button"
                      // Removing a calculated helper subtracts its value from
                      // the running total; a normal helper just drops the box.
                      onClick={() => (row.is_calculated ? onCalculatedRemove?.(idx) : onHelperRemove(idx))}
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
          {(row.is_calculated || row.has_multiple_text_box) && canAdd && !locked && (
            <button
              type="button"
              // Calculated questions run the validate + fold-into-helper flow;
              // other multi-text-box questions just append an empty helper.
              onClick={row.is_calculated ? onCalculatedAdd : onHelperAdd}
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
