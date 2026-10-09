/**
 * TemplateDrivenSnip — the single grid component for EVERY format type.
 *
 * Renders one <th>/cell per column configured in Template Studio
 * (template_layout_columns), in display_order, by column_type
 * (SERIAL / QUESTION / OPTION / ANSWER / RESPONSE / AQL_LIMIT). Supports:
 *   - flat stages (one table from the stage's own columns), and
 *   - sectioned stages (a header + table per section, each using that
 *     section's own columns), and
 *   - sub-questions (shown nested under their parent question).
 *
 * If a stage/section has no columns configured, nothing is rendered — a
 * "not configured" message is shown instead of a fallback grid.
 *
 * Exposes validate()/getAnswers() via ref. Answer state + validation live in
 * useValidateTemplateAnswers, which is fed the FLATTENED question list (stage
 * questions + every section's questions) so validate/getAnswers cover the
 * whole stage regardless of layout.
 */

import { forwardRef, useImperativeHandle } from 'react';
import { BASIC_DETAILS_STAGE } from '../../masters/constants';
import type { ChecklistStagePreview, ColumnPreview, QuestionAnswerPreview, SectionPreview } from '../models/ChecklistPreview';
import type { TemplateDrivenSnipHandle } from '../models/TemplateTypes';
import type { SavedAnswer } from '../hooks/useValidateTemplateAnswers';
import { useResolvedColumns } from '../hooks/useResolvedColumns';
import { useValidateTemplateAnswers } from '../hooks/useValidateTemplateAnswers';
import { TemplateCell } from './TemplateCell';

export type { TemplateDrivenSnipHandle } from '../models/TemplateTypes';

interface Props {
  questions: ChecklistStagePreview['questions'];
  columns: ColumnPreview[];
  stageName: string;
  stageStatus: string;
  /** Section groups for a sectioned stage (each carries its own columns). */
  sections?: SectionPreview[];
  hasSection?: boolean;
  /** Pre-loaded saved answers keyed by stage_question_mapping_id (read-only view). */
  savedAnswers?: Record<number, SavedAnswer>;
}

export const TemplateDrivenSnip = forwardRef<TemplateDrivenSnipHandle, Props>(
  ({ questions, columns, stageName, stageStatus, sections = [], hasSection = false, savedAnswers }, ref) => {
    const isBasicDetails = stageName === BASIC_DETAILS_STAGE;
    // Editable only while the stage is still fillable; once submitted
    // (Pending) or approved it's view-only until the approver acts.
    const canAdd = stageStatus === 'Initial' || stageStatus === 'Draft' || stageStatus === 'ReferBack';

    // Flatten every question the stage carries — flat questions or all section
    // questions — so the answer hook validates/returns the whole stage.
    const allQuestions: QuestionAnswerPreview[] = hasSection
      ? sections.flatMap((s) => s.questions)
      : questions;

    // Column-type flags are derived from the union of stage + section columns,
    // so option/answer/response validation applies regardless of where the
    // columns live.
    const unionColumns = hasSection ? sections.flatMap((s) => s.columns) : columns;
    const { hasOptionColumn, hasAnswerColumn, hasResponseColumn } = useResolvedColumns(unionColumns, isBasicDetails);

    const {
      selections, setSelections,
      answers, setAnswers,
      responses, setResponses,
      helpers, setHelpers,
      errors, helperErrors, clearError, clearHelperError,
      validate, getAnswers,
    } = useValidateTemplateAnswers({
      questions: allQuestions, hasOptionColumn, hasAnswerColumn, hasResponseColumn, isBasicDetails, savedAnswers,
    });

    useImperativeHandle(ref, () => ({ validate, getAnswers }));

    /** Render one table for a given set of columns + question rows. */
    const renderTable = (cols: ColumnPreview[], rows: QuestionAnswerPreview[], keyPrefix: string) => {
      const orderedColumns = cols
        .filter((c) => c.column_type !== 'RESPONSE' || !isBasicDetails)
        .slice()
        .sort((a, b) => a.display_order - b.display_order);

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
              {rows.map((row) => {
                const key = row.stage_question_mapping_id;
                return (
                  <tr key={`${keyPrefix}-${key}`} style={{ borderBottom: '1px solid #f1f5f9' }}>
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
    };

    if (allQuestions.length === 0) {
      return <div style={{ padding: '1rem', color: '#94a3b8', fontSize: '0.78rem' }}>No questions for this stage.</div>;
    }

    // Sectioned stage — one labelled table per section (each uses its columns).
    if (hasSection) {
      return (
        <div style={{ overflow: 'auto' }}>
          {sections.map((section) => (
            <div key={section.section_id}>
              {section.section_name && (
                <div style={{
                  padding: '0.5rem 0.75rem', fontWeight: 700, fontSize: '0.8rem',
                  color: 'var(--color-primary)', background: '#fef2f2', borderBottom: '1px solid #fecaca',
                }}>
                  {section.section_name}
                </div>
              )}
              {renderTable(section.columns, section.questions, `sec${section.section_id}`)}
            </div>
          ))}
        </div>
      );
    }

    // Flat stage — a single table from the stage's own columns.
    return renderTable(columns, questions, 'flat');
  }
);

TemplateDrivenSnip.displayName = 'TemplateDrivenSnip';
