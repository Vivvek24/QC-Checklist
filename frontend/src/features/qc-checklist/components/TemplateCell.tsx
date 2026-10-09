/**
 * TemplateCell — renders a single cell of TemplateDrivenSnip's grid, branching
 * on the column's column_type. Pure presentational: all state lives in the
 * caller (useValidateTemplateAnswers) and is passed in / mutated via callbacks.
 */

import { InputText } from 'primereact/inputtext';
import { RadioButton } from 'primereact/radiobutton';
import { OptionSelector } from './OptionSelector';
import type { ColumnPreview } from '../models/ChecklistPreview';
import type { QuestionAnswerPreview } from '../models/TemplateTypes';
import type { RowErrors } from '../hooks/useValidateTemplateAnswers';

type ColumnLike = Pick<ColumnPreview, 'column_type'>;

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
}

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
          {row.has_sub_question && (row.sub_questions?.length ?? 0) > 0 && (
            <div style={{ marginTop: '0.3rem', paddingLeft: '0.75rem' }}>
              {row.sub_questions!.map((sub) => (
                <div key={sub.question_id} style={{ fontSize: '0.72rem', color: '#64748b', marginBottom: '0.2rem' }}>
                  • {sub.question_title}
                </div>
              ))}
            </div>
          )}
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
      if (showNA) return <span style={{ color: '#94a3b8', fontSize: '0.78rem' }}>N/A</span>;
      return (
        <div className="flex flex-column gap-1">
          <InputText
            value={answer}
            className={rowErr?.answer ? 'w-full p-invalid' : 'w-full'}
            onChange={(e) => onAnswerChange(e.target.value)}
            disabled={locked}
            style={{ height: '1.85rem', fontSize: '0.75rem' }}
          />
          {rowErr?.answer && <small className="qc-validation-error">{rowErr.answer}</small>}
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
        </div>
      );
    }
  }
};
