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

import { forwardRef, useImperativeHandle, useRef, useState, type ReactNode } from 'react';
import { Button } from 'primereact/button';
import { Toast } from 'primereact/toast';
import { IssueVialsDialog } from './IssueVialsDialog';
import { qcChecklistApi } from '../api/qcChecklistApi';
import type { ChecklistStagePreview, ColumnPreview, QuestionAnswerPreview, SectionPreview } from '../models/ChecklistPreview';
import type { TemplateDrivenSnipHandle } from '../models/TemplateTypes';
import type { SavedAnswer, SavedSubAnswer } from '../hooks/useValidateTemplateAnswers';
import type { TestRow } from '../hooks/useChecklistWorkflow';
import type { ApprovalLabelMappingResponse } from '../api/qcChecklistApi';
import { useTemplateDrivenSnip } from '../hooks/useTemplateDrivenSnip';
import { useMenuPermission } from '@core/rbac/usePermissions';
import { TemplateCell } from './TemplateCell';

export type { TemplateDrivenSnipHandle } from '../models/TemplateTypes';

/** With table-layout: fixed, columns keep their configured width and long
 * content wraps (growing the row's HEIGHT) instead of widening the column. */
const WRAP_STYLE = {
  whiteSpace: 'normal' as const,
  wordBreak: 'break-word' as const,
  overflowWrap: 'anywhere' as const,
};

/** Default width for a column that has no configured width — so table-layout:
 * fixed still has a size to honor. */
const DEFAULT_COL_WIDTH = '10rem';
const colWidth = (c: { column_type: string; width: string | null }): string =>
  c.width ?? (c.column_type === 'SERIAL' ? '4rem' : DEFAULT_COL_WIDTH);

/** Format an ISO datetime string as dd-mm-yyyy hh:mm (24h); '—' when empty. */
const fmtDateTime = (iso: string | null): string => {
  if (!iso) return '—';
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return '—';
  const pad = (n: number) => String(n).padStart(2, '0');
  return `${pad(d.getDate())}-${pad(d.getMonth() + 1)}-${d.getFullYear()} ${pad(d.getHours())}:${pad(d.getMinutes())}`;
};

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
  /** Pre-loaded saved sub-answers keyed by parent question_id. */
  savedSubAnswers?: Record<number, SavedSubAnswer[]>;
  /** Loaded per-question approval mappings for this request (keyed by question_answer_id). */
  questionApprovalMappings?: ApprovalLabelMappingResponse[];
  /** question_answer_id -> stage_question_mapping_id, from the loaded answers. */
  sqmByQuestionAnswerId?: Record<number, number>;
  /** Auto-generated per-test rows (no stage_question_mapping) — rendered as a
   * read-only table whose TEST_TITLE/SAMPLE_VIAL cells show each test's name
   * and sample description. Used by the sample recon sheet stage, which has
   * no configured questions. */
  testRows?: TestRow[];
  /** Fired when a Masters product is picked on this grid — the page uses it to
   * preview the per-test rows the product expands into on the next stage. */
  onProductSelected?: (productId: number | null) => void;
  /** Resolve an acting user's id to a display name (for acted approval rows). */
  userNameById?: (userId: number) => string;
  /** True when the request's format is ReconcilationSheet — relaxes the
   * calculated-total + helper required checks at submit. */
  isReconSheet?: boolean;
  /** Recon analyst phase: make ONLY the is_calculated question editable on an
   * otherwise read-only (Pending) Basic Details stage so the analyst can fill
   * "Sample Quantity Received". Every other row stays locked. */
  unlockCalculated?: boolean;
}

export const TemplateDrivenSnip = forwardRef<TemplateDrivenSnipHandle, Props>(
  ({ questions, columns, stageName, stageStatus, sections = [], hasSection = false, savedAnswers, savedSubAnswers, questionApprovalMappings, sqmByQuestionAnswerId, testRows = [], onProductSelected, userNameById, isReconSheet = false, unlockCalculated = false }, ref) => {
    const {
      allQuestions, canAdd, isBasicDetails,
      selections, setSelections,
      answers, setAnswers,
      responses, setResponses,
      responseOptionSelections, setResponseOptionSelections,
      productSelections, onProductPicked, productOptions,
      dateSelections, setDateSelections,
      helpers, setHelpers,
      totals, addCalculatedHelper, removeCalculatedHelper, validateCalculatedValue,
      errors, helperErrors, clearError, clearHelperError,
      sapTriggerKey, fetchFromSap, sapLoading, sapError,
      subAccess, approvalAccess,
      validateAll, getAnswers, getQuestionApprovals,
    } = useTemplateDrivenSnip({
      questions, columns, stageName, stageStatus, sections, hasSection, isReconSheet,
      savedAnswers, savedSubAnswers, questionApprovalMappings, sqmByQuestionAnswerId, userNameById,
    });

    useImperativeHandle(ref, () => ({ validate: validateAll, getAnswers, getQuestionApprovals }));

    // The test row whose "Issue Vials" button is open (null = dialog closed).
    const [issuingRowId, setIssuingRowId] = useState<number | null>(null);
    // Post-save overlay keyed by row id — lets an issued row reflect its new
    // issuer/receiver/dates immediately without re-loading the whole stage.
    const [issuedOverlay, setIssuedOverlay] = useState<Record<number, Partial<TestRow>>>({});
    // Issue Vials visibility is permission-driven (seeded menu key), not a
    // hardcoded role check — granted to SUPERVISOR via seed_rbac.
    const { canAccess: canIssueVials } = useMenuPermission('qc_checklist.issue_vials');
    const toast = useRef<Toast>(null);

    // Apply any post-save overlay so a freshly-issued row renders its new state.
    const withOverlay = (row: TestRow): TestRow => ({ ...row, ...issuedOverlay[row.id] });

    // Persist the Issue Vials action for the open row. The server records the
    // receiving analyst, stamps the issue/received dates + issuer, and sets the
    // Basic Details analysis start date if it's still empty.
    const handleIssueVials = async (receiverUserId: number) => {
      if (issuingRowId == null || issuingRowId < 0) return; // only persisted rows
      const rowId = issuingRowId;
      try {
        const updated = await qcChecklistApi.issueVials(rowId, receiverUserId);
        setIssuedOverlay((prev) => ({
          ...prev,
          [rowId]: {
            receiver_user_id: updated.receiver_user_id ?? null,
            receiver_name: updated.receiver_name || '',
            issuer_name: updated.issuer_name || '',
            issued_by_date: updated.issued_by_date ?? null,
            received_by_date: updated.received_by_date ?? null,
            is_issued_vails: updated.is_issued_vails ?? true,
          },
        }));
        toast.current?.show({
          severity: 'success', summary: 'Vials issued',
          detail: 'The vials were issued to the selected analyst.', life: 3000,
        });
      } catch {
        toast.current?.show({
          severity: 'error', summary: 'Issue failed',
          detail: 'Could not issue the vials. Please try again.', life: 5000,
        });
      }
    };

    /** Render one table for a given set of columns + question rows.
     * Declaration questions are excluded — they render in the ApprovalSnip. */
    const renderTable = (cols: ColumnPreview[], allRows: QuestionAnswerPreview[], keyPrefix: string) => {
      const rows = allRows.filter((r) => !r.is_declaration_question);
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
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.78rem', tableLayout: 'fixed' }}>
            <thead>
              <tr style={{ background: '#f8fafc' }}>
                {orderedColumns.map((c, i) => (
                  <th
                    key={i}
                    style={{
                      padding: '0.5rem 0.75rem',
                      textAlign: c.column_type === 'SERIAL' ? 'center' : 'left',
                      fontWeight: 700, color: '#475569',
                      width: colWidth(c),
                      ...WRAP_STYLE,
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
                          verticalAlign: 'top',
                          ...WRAP_STYLE,
                        }}
                      >
                        <TemplateCell
                          column={c}
                          row={row}
                          // Recon analyst phase: the is_calculated row stays
                          // editable even when the rest of the stage is locked.
                          canAdd={canAdd || (unlockCalculated && row.is_calculated)}
                          disabled={!canAdd && !(unlockCalculated && row.is_calculated)}
                          rowErr={errors[key]}
                          isSapTrigger={sapTriggerKey != null && key === sapTriggerKey}
                          sapLoading={sapLoading}
                          sapError={sapError}
                          onSapFetch={fetchFromSap}
                          selection={selections[key] ?? null}
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
                          responseOption={responseOptionSelections[key] ?? null}
                          onResponseOptionChange={(val) => {
                            setResponseOptionSelections((prev) => ({ ...prev, [key]: val }));
                            clearError(key, 'responseOption');
                          }}
                          productOptions={productOptions}
                          productValue={productSelections[key] ?? null}
                          onProductChange={(val) => {
                            // Records the selection + auto-fills any
                            // has_associated_master question with the product's
                            // storage conditions.
                            onProductPicked(key, val);
                            clearError(key, 'product');
                            // Preview the next stage's per-test rows for the
                            // picked product (persisted only on submit).
                            onProductSelected?.(val);
                          }}
                          dateValue={dateSelections[key] ?? null}
                          onDateChange={(val) => {
                            setDateSelections((prev) => ({ ...prev, [key]: val }));
                            clearError(key, 'date');
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
                          subAccess={subAccess}
                          approvalAccess={approvalAccess}
                          canIssueVials={canIssueVials}
                          onIssueVials={() => setIssuingRowId(key)}
                          answerTotalVails={totals[key] ?? 0}
                          onCalculatedAdd={() => addCalculatedHelper(key)}
                          onCalculatedRemove={(idx) => removeCalculatedHelper(key, idx)}
                          onCalculatedChange={(val) => validateCalculatedValue(key, val)}
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

    /** Render the auto-generated per-test rows as a read-only table. These
     * rows have no stage_question_mapping/question; each row's TEST_TITLE cell
     * shows the test name and SAMPLE_VIAL shows the sample description. Other
     * column types render blank (SERIAL shows the running index). */
    const renderTestTable = (cols: ColumnPreview[], rows: TestRow[], keyPrefix: string) => {
      const orderedColumns = cols.slice().sort((a, b) => a.display_order - b.display_order);
      if (orderedColumns.length === 0 || rows.length === 0) return null;

      const renderCell = (c: ColumnPreview, row: TestRow, idx: number): ReactNode => {
        switch (c.column_type) {
          case 'SERIAL': return String(idx + 1);
          case 'TEST_TITLE': return row.test_title;
          case 'SAMPLE_VIAL': return row.sample_vails;
          case 'ISSUE_VAILS': {
            // Button visibility (Mendix): trim(IssuerName) == '' AND hasVails.
            // Issuing/re-picking is a permission-gated action (seeded menu
            // key) — only users with that grant (supervisor) see the Issue
            // Vials / Edit buttons. But the resulting issuer name + issue date
            // are plain data: once a row is issued everyone (incl. the analyst
            // who lacks the action permission) must see who issued it and when.
            const notYetIssued = (row.issuer_name ?? '').trim() === '';
            if (notYetIssued) {
              // Nothing issued yet: only the action-holder sees the button,
              // and only for vial-bearing rows. Everyone else sees blank.
              if (!canIssueVials || !row.has_vails) return '';
              return (
                <Button
                  label="Issue Vials"
                  icon="pi pi-send"
                  size="small"
                  outlined
                  type="button"
                  onClick={() => setIssuingRowId(row.id)}
                  style={{ fontSize: '0.7rem', padding: '0.3rem 0.6rem' }}
                />
              );
            }
            // Already issued: show the issuer name + date to everyone. The
            // Edit (re-pick receiver) button stays gated on the permission AND
            // only while the Test stage is still in its issuing/fill phase
            // (Initial/Draft/ReferBack). Once the analyst submits for approval
            // the stage leaves that phase (→ Pending/…), so re-picking is
            // locked and the Edit button is hidden from everyone.
            const stillIssuing = ['Initial', 'Draft', 'ReferBack'].includes(stageStatus);
            return (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.2rem' }}>
                <span style={{ fontWeight: 600, color: '#334155' }}>{row.issuer_name}</span>
                <span style={{ fontSize: '0.72rem', color: '#64748b' }}>{fmtDateTime(row.issued_by_date)}</span>
                {canIssueVials && stillIssuing && (
                  <Button
                    label="Edit"
                    icon="pi pi-pencil"
                    size="small"
                    text
                    type="button"
                    onClick={() => setIssuingRowId(row.id)}
                    style={{ fontSize: '0.7rem', padding: '0.2rem 0.4rem', alignSelf: 'flex-start' }}
                  />
                )}
              </div>
            );
          }
          case 'RECEIVE_VIALS':
            // Visible only once a receiver is set (Mendix: receiver != empty).
            // Shows the receiver's full name + the received date/time.
            if (!row.receiver_user_id) return '';
            return (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.2rem' }}>
                <span style={{ fontWeight: 600, color: '#334155' }}>{row.receiver_name || '—'}</span>
                <span style={{ fontSize: '0.72rem', color: '#64748b' }}>{fmtDateTime(row.received_by_date)}</span>
              </div>
            );
          default: return '';
        }
      };

      return (
        <div style={{ overflow: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.78rem', tableLayout: 'fixed' }}>
            <thead>
              <tr style={{ background: '#f8fafc' }}>
                {orderedColumns.map((c, i) => (
                  <th
                    key={i}
                    style={{
                      padding: '0.5rem 0.75rem',
                      textAlign: c.column_type === 'SERIAL' ? 'center' : 'left',
                      fontWeight: 700, color: '#475569',
                      width: colWidth(c),
                      ...WRAP_STYLE,
                      borderBottom: '1px solid #e2e8f0',
                    }}
                  >
                    {c.header}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {rows.map((raw, ri) => {
                const row = withOverlay(raw);
                return (
                  <tr key={`${keyPrefix}-${row.id}`} style={{ borderBottom: '1px solid #f1f5f9' }}>
                    {orderedColumns.map((c, i) => (
                      <td
                        key={i}
                        style={{
                          padding: '0.5rem 0.75rem',
                          textAlign: c.column_type === 'SERIAL' ? 'center' : 'left',
                          color: '#1e293b',
                          verticalAlign: 'top',
                          ...WRAP_STYLE,
                        }}
                      >
                        {renderCell(c, row, ri)}
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

    // The Issue Vials popup — mounted wherever test rows render. onIssue gets
    // the picked analyst user id for the row being issued.
    const issueVialsDialog = (
      <>
        <Toast ref={toast} />
        <IssueVialsDialog
          visible={issuingRowId != null}
          onHide={() => setIssuingRowId(null)}
          onIssue={(userId) => { void handleIssueVials(userId); }}
        />
      </>
    );

    // A stage with no configured questions but with auto-generated test rows
    // (the sample recon sheet): render just the test-row table.
    if (allQuestions.length === 0) {
      if (testRows.length > 0) {
        return <>{renderTestTable(columns, testRows, 'test')}{issueVialsDialog}</>;
      }
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

    // Flat stage — the stage's own question table, plus (if any) the
    // auto-generated test-row table below it.
    return (
      <>
        {renderTable(columns, questions, 'flat')}
        {testRows.length > 0 && renderTestTable(columns, testRows, 'test')}
        {issueVialsDialog}
      </>
    );
  }
);

TemplateDrivenSnip.displayName = 'TemplateDrivenSnip';
