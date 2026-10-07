/**
 * TemplateDrivenSnip — grid component for any format type, rendered from
 * the checklist column layout configured in Template Studio
 * (template_layout_columns) instead of a hardcoded per-format-type table.
 *
 * Replaces the old approach (one hardcoded Snip component per format type —
 * ChromatographicSnip, etc.) with a single generic renderer: one <th>/cell
 * per configured column, in display_order, rendered according to its
 * column_type (SERIAL / QUESTION / OPTION / ANSWER / RESPONSE / AQL_LIMIT).
 *
 * If a stage has no columns configured in Template Studio, nothing is
 * rendered — a "not configured" message is shown instead of a fallback
 * grid. See useResolvedColumns.
 *
 * Exposes validate()/getAnswers() via ref — the same contract the old
 * per-format Snip components used — so CreateRequestPage's submit/draft flow
 * doesn't need to change. Answer state and validation live in useValidateTemplateAnswers;
 * this component is just layout + wiring cells to that state.
 */

import { forwardRef, useImperativeHandle } from 'react';
import { BASIC_DETAILS_STAGE } from '../../masters/constants';
import type { ColumnPreview } from '../models/ChecklistPreview';
import type { QuestionAnswerPreview, TemplateDrivenSnipHandle } from '../models/TemplateTypes';
import type { SavedAnswer } from '../hooks/useValidateTemplateAnswers';
import { useResolvedColumns } from '../hooks/useResolvedColumns';
import { useValidateTemplateAnswers } from '../hooks/useValidateTemplateAnswers';
import { TemplateCell } from './TemplateCell';

export type { TemplateDrivenSnipHandle } from '../models/TemplateTypes';

interface Props {
  questions: QuestionAnswerPreview[];
  columns: ColumnPreview[];
  stageName: string;
  stageStatus: string;
  /** Pre-loaded saved answers keyed by stage_question_mapping_id (for read-only view). */
  savedAnswers?: Record<number, SavedAnswer>;
}

export const TemplateDrivenSnip = forwardRef<TemplateDrivenSnipHandle, Props>(
  ({ questions, columns, stageName, stageStatus, savedAnswers }, ref) => {
    const isBasicDetails = stageName === BASIC_DETAILS_STAGE;
    // Editable only while the stage is still fillable; once submitted
    // (Pending) or approved it's view-only until the approver acts.
    const canAdd = stageStatus === 'Initial' || stageStatus === 'Draft' || stageStatus === 'ReferBack';

    const { orderedColumns, hasOptionColumn, hasAnswerColumn, hasResponseColumn } = useResolvedColumns(
      columns,
      isBasicDetails
    );

    const {
      selections, setSelections,
      answers, setAnswers,
      responses, setResponses,
      helpers, setHelpers,
      errors, helperErrors, clearError, clearHelperError,
      validate, getAnswers,
    } = useValidateTemplateAnswers({ questions, hasOptionColumn, hasAnswerColumn, hasResponseColumn, isBasicDetails, savedAnswers });

    useImperativeHandle(ref, () => ({ validate, getAnswers }));

    if (questions.length === 0) {
      return <div style={{ padding: '1rem', color: '#94a3b8', fontSize: '0.78rem' }}>No questions for this stage.</div>;
    }

    if (orderedColumns.length === 0) {
      return (
        <div style={{ padding: '1rem', color: '#94a3b8', fontSize: '0.78rem' }}>
          No column layout configured for this stage in Template Studio.
        </div>
      );
    }

    return (
      <div style={{ overflow: 'auto' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.78rem' }}>
          <thead>
            <tr style={{ background: '#f8fafc' }}>
              {orderedColumns.map((c, i) => (
                <th
                  key={i}
                  style={{
                    padding: '0.5rem 0.75rem',
                    textAlign: c.column_type === 'SERIAL' ? 'center' : 'left',
                    fontWeight: 700, color: '#475569',
                    width: c.width ?? undefined,
                    borderBottom: '1px solid #e2e8f0',
                  }}
                >
                  {c.header}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {questions.map((row) => {
              const key = row.stage_question_mapping_id;
              return (
                <tr key={key} style={{ borderBottom: '1px solid #f1f5f9' }}>
                  {orderedColumns.map((c, i) => (
                    <td
                      key={i}
                      style={{
                        padding: '0.5rem 0.75rem',
                        textAlign: c.column_type === 'SERIAL' ? 'center' : 'left',
                      }}
                    >
                      <TemplateCell
                        column={c}
                        row={row}
                        canAdd={canAdd}
                        disabled={!canAdd}
                        rowErr={errors[key]}
                        selection={selections[key]}
                        onSelectionChange={(val) => {
                          setSelections((prev) => ({ ...prev, [key]: val }));
                          clearError(key, 'options');
                        }}
                        answer={answers[key] || ''}
                        onAnswerChange={(val) => {
                          setAnswers((prev) => ({ ...prev, [key]: val }));
                          clearError(key, 'answer');
                        }}
                        response={responses[key] || ''}
                        onResponseChange={(val) => {
                          setResponses((prev) => ({ ...prev, [key]: val }));
                          clearError(key, 'response');
                        }}
                        helperValues={helpers[key] || []}
                        helperErrors={helperErrors[key]}
                        onHelperChange={(idx, val) => {
                          setHelpers((prev) => {
                            const arr = [...(prev[key] || [])];
                            arr[idx] = val;
                            return { ...prev, [key]: arr };
                          });
                          clearHelperError(key, idx);
                        }}
                        onHelperRemove={(idx) =>
                          setHelpers((prev) => {
                            const arr = [...(prev[key] || [])];
                            arr.splice(idx, 1);
                            return { ...prev, [key]: arr };
                          })
                        }
                        onHelperAdd={() => setHelpers((prev) => ({ ...prev, [key]: [...(prev[key] || []), ''] }))}
                      />
                    </td>
                  ))}
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    );
  }
);

TemplateDrivenSnip.displayName = 'TemplateDrivenSnip';
