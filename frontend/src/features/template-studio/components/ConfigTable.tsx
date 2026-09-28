/**
 * ConfigTable — the reusable columns+rows preview table used by both a stage
 * and a section.
 *
 * Columns have an editable header, a type (Sr No / Question / Select Option /
 * Enter Answer / Yes-No-N-A / AQL Limit), a required toggle, an editable width,
 * and reorder controls. Rows pick a question; Option / AQL / answer cells
 * auto-derive from that question — including its answer_type, multiple answer
 * boxes, and sub-questions.
 */

import { useRef, useState } from 'react';
import { InputText } from 'primereact/inputtext';
import { Dropdown } from 'primereact/dropdown';
import { Calendar } from 'primereact/calendar';
import { RadioButton } from 'primereact/radiobutton';
import { Button } from 'primereact/button';
import { InputSwitch } from 'primereact/inputswitch';
import { OverlayPanel } from 'primereact/overlaypanel';
import { Tag } from 'primereact/tag';
import { useDragReorder } from '../hooks/useDragReorder';
import type { DesignColumn, DesignRow } from '../models/DesignSpec';
import { COLUMN_RENDERS, newColumnKey, newRowKey } from '../models/DesignSpec';

/** SAP field option for the per-row settings. */
export interface SapFieldOption {
  id: number;
  label: string;
}

/** Custom answer option (Reconciliation). */
export interface CustomAnswerOption {
  label: string;
  value: string;
}

const BASIC_DETAILS_STAGE = 'Basic Details';

/** A sub-question, with the same answer-relevant fields as a question. */
export interface SubQuestionChoice {
  id: number;
  title: string;
  answerType: string;
  hasTextBox: boolean;
  hasMultipleTextBox: boolean;
  options: { id: number; label: string }[];
}

/** A question available to pick, with its configured answer behaviour. */
export interface QuestionChoice {
  id: number;
  title: string;
  answerType: string;
  hasTextBox: boolean;
  hasMultipleTextBox: boolean;
  hasSubQuestion: boolean;
  masterType: string | null;
  options: { id: number; label: string }[];
  aqlLimit: string;
  subQuestions: SubQuestionChoice[];
}

/** Format-level context shared by every stage/section table. */
export interface MappingContext {
  formatType: string;
  hasDeclarationQuestion: boolean;
  sapFields: SapFieldOption[];
  customAnswerOptions: CustomAnswerOption[];
}

interface Props {
  columns: DesignColumn[];
  rows: DesignRow[];
  questionChoices: QuestionChoice[];
  /** The stage this table belongs to (drives per-row attribute visibility). */
  stageName: string;
  /** Format-level context. */
  ctx: MappingContext;
  onColumnsChange: (columns: DesignColumn[]) => void;
  onRowsChange: (rows: DesignRow[]) => void;
  /** Called with a row's backing mappingId when a saved row is removed, so Save can delete it. */
  onRowDeleted?: (mappingId: number) => void;
}

const typeOptions = COLUMN_RENDERS.map((r) => ({ label: r.label, value: r.render }));

/**
 * The width field only ever shows a plain number — "rem" is applied silently
 * underneath. Typing "8" stores "8rem"; the field itself keeps showing "8".
 */
const widthToNumber = (width: string | undefined): string => {
  if (!width) return '';
  const match = /^(\d+(?:\.\d+)?)rem$/.exec(width);
  return match ? match[1]! : width;
};

const numberToWidth = (raw: string): string | undefined => {
  // Keep only digits and a single decimal point as the user types.
  const cleaned = raw.replace(/[^\d.]/g, '');
  if (!cleaned) return undefined;
  return `${cleaned}rem`;
};

/**
 * Turns a stored column width ("8rem") into a responsive CSS value: it grows
 * up to the typed width on wide screens, but can shrink down to a smaller
 * floor when space is tight (sidebar open, narrow window, phone), instead of
 * staying rigid and forcing the whole table to horizontally scroll.
 */
const columnWidthStyle = (width: string | undefined): string | undefined => {
  if (!width) return undefined;
  const match = /^(\d+(?:\.\d+)?)rem$/.exec(width);
  if (!match) return width;
  const target = parseFloat(match[1]!);
  const floor = Math.min(target, 5.5);
  return `clamp(${floor}rem, 12vw, ${target}rem)`;
};

/**
 * An answer input driven purely by an answer_type (used for both questions
 * and sub-questions). Dropdown/multi-select answer types are handled by the
 * Select Option column instead — this input never renders a dropdown.
 */
const AnswerInput = ({
  answerType,
  hasTextBox,
  hasMultipleTextBox,
  masterType,
  placeholder,
}: {
  answerType: string;
  hasTextBox: boolean;
  hasMultipleTextBox: boolean;
  masterType?: string | null;
  placeholder?: string;
}) => {
  const [helpers, setHelpers] = useState<string[]>([]);
  const small = { height: '1.8rem', fontSize: '0.75rem' } as const;

  // Answer-type-aware main control. Dropdown/multi-select answer types belong
  // exclusively to the Select Option column — the Enter Answer column never
  // renders a dropdown, even if the question's answer_type is a dropdown.
  let main: React.ReactNode;
  switch (answerType) {
    case 'Dropdown (single select)':
    case 'Dropdown (multi select)':
      main = <span style={{ color: '#94a3b8', fontSize: '0.75rem' }}>N/A — see Select Option column</span>;
      break;
    case 'Date & Time':
      main = <Calendar showTime hourFormat="24" className="w-full" inputStyle={small} placeholder={placeholder} />;
      break;
    case 'Masters':
      main = (
        <Dropdown
          options={[]}
          placeholder={masterType ? `${masterType} lookup` : 'Master lookup'}
          className="w-full"
          style={small}
          disabled
          emptyMessage="from master"
        />
      );
      break;
    case 'None':
      main = <span style={{ color: '#94a3b8', fontSize: '0.75rem' }}>N/A</span>;
      break;
    case 'Text Box':
    default:
      main = <InputText placeholder={placeholder ?? ''} className="w-full" style={small} disabled />;
      break;
  }

  const showHelpers = hasMultipleTextBox && (answerType === 'Text Box' || hasTextBox);

  return (
    <div className="flex flex-column gap-1">
      {main}
      {showHelpers && (
        <>
          {helpers.map((val, idx) => (
            <div key={idx} className="flex align-items-center gap-1">
              <InputText
                value={val}
                onChange={(e) => setHelpers((p) => p.map((v, i) => (i === idx ? e.target.value : v)))}
                className="flex-1"
                style={small}
                disabled
              />
              <Button
                icon="pi pi-times" rounded text severity="danger" size="small"
                onClick={() => setHelpers((p) => p.filter((_, i) => i !== idx))} type="button"
                style={{ width: '1.4rem', height: '1.4rem' }}
              />
            </div>
          ))}
          <Button
            label="Add" icon="pi pi-plus" size="small" text
            onClick={() => setHelpers((p) => [...p, ''])} type="button"
            style={{ width: 'fit-content', fontSize: '0.68rem', padding: '0.1rem 0.4rem' }}
          />
        </>
      )}
    </div>
  );
};

/** YES / NO / N-A radio group. */
const ResponseInput = ({ name }: { name: string }) => {
  const [val, setVal] = useState('');
  return (
    <div className="flex align-items-center gap-2">
      {['YES', 'NO', 'N/A'].map((v) => (
        <div key={v} className="flex align-items-center gap-1">
          <RadioButton inputId={`${name}_${v}`} name={name} value={v} checked={val === v} onChange={() => setVal(v)} />
          <label htmlFor={`${name}_${v}`} style={{ fontSize: '0.7rem' }}>{v}</label>
        </div>
      ))}
    </div>
  );
};

export const ConfigTable = ({ columns, rows, questionChoices, stageName, ctx, onColumnsChange, onRowsChange, onRowDeleted }: Props) => {
  const settingsOp = useRef<OverlayPanel>(null);
  const [settingsRowKey, setSettingsRowKey] = useState<string | null>(null);

  // Inline validation, scoped to this table's own rows (a stage's direct rows
  // and each section's rows are validated independently — matching the
  // original form, which only enforces uniqueness per format_stage_mapping_id
  // + section_id). A row with no question picked is missing; a question
  // picked on more than one row in the same table is a duplicate. Both are
  // highlighted directly on the offending row's Question cell instead of a
  // generic toast, and Save is blocked while any of this table's rows have
  // either problem (see handleSaveAll's pre-flight check).
  const missingQuestionKeys = new Set(rows.filter((r) => !r.questionId).map((r) => r.key));
  const questionCounts = new Map<number, number>();
  for (const r of rows) {
    if (r.questionId) questionCounts.set(r.questionId, (questionCounts.get(r.questionId) ?? 0) + 1);
  }
  const duplicateRowKeys = new Set(
    rows.filter((r) => r.questionId && (questionCounts.get(r.questionId) ?? 0) > 1).map((r) => r.key)
  );

  // Per-row attribute visibility — mirrors AddStageQuestionForm rules.
  const isBasicDetails = stageName === BASIC_DETAILS_STAGE;
  const isAQL = ctx.formatType === 'AQL';
  const isReconcilation = ctx.formatType === 'ReconcilationSheet';
  const showShowOnGrid = isBasicDetails;
  const showSapField = isBasicDetails && isAQL;
  const showIsEditable = isBasicDetails && (isAQL || isReconcilation);
  const showDeclaration = ctx.hasDeclarationQuestion && !isBasicDetails;
  const showCustomAnswers = isReconcilation;
  const showAqlLimit = isAQL;

  const sapFieldOptions = ctx.sapFields.map((s) => ({ label: s.label, value: s.id }));
  const customAnswerOptions = ctx.customAnswerOptions;
  const addColumn = () =>
    onColumnsChange([
      ...columns,
      { key: newColumnKey(), header: 'Enter Answer', render: 'ANSWER', width: '10rem' },
    ]);
  const patchColumn = (key: string, fields: Partial<DesignColumn>) =>
    onColumnsChange(columns.map((c) => (c.key === key ? { ...c, ...fields } : c)));
  const removeColumn = (key: string) => onColumnsChange(columns.filter((c) => c.key !== key));
  const moveColumn = (key: string, dir: -1 | 1) => {
    const i = columns.findIndex((c) => c.key === key);
    const j = i + dir;
    if (i < 0 || j < 0 || j >= columns.length) return;
    const next = [...columns];
    const a = next[i];
    const b = next[j];
    if (!a || !b) return;
    next[i] = b;
    next[j] = a;
    onColumnsChange(next);
  };

  const addRow = () => onRowsChange([...rows, { key: newRowKey() }]);
  const removeRow = (key: string) => {
    const row = rows.find((r) => r.key === key);
    if (row?.mappingId) onRowDeleted?.(row.mappingId);
    onRowsChange(rows.filter((r) => r.key !== key));
  };
  const patchRow = (key: string, fields: Partial<DesignRow>) =>
    onRowsChange(rows.map((r) => (r.key === key ? { ...r, ...fields } : r)));

  // Drag-and-drop reordering for rows — native HTML5 DnD via the shared hook.
  // Reordering here changes the row's position, which changes its saved
  // serial_number on the next Save (serial is derived from array index).
  const rowDrag = useDragReorder<DesignRow>({ items: rows, onReorder: onRowsChange });

  const questionDropdownOptions = questionChoices.map((q) => ({ label: q.title, value: q.id }));
  const rowQuestion = (row: DesignRow) => questionChoices.find((q) => q.id === row.questionId);

  const pickRowQuestion = (rowKey: string, questionId: number | null) => {
    const q = questionChoices.find((x) => x.id === questionId);
    patchRow(rowKey, { questionId: questionId ?? undefined, questionTitle: q?.title });
  };

  const needQuestion = (
    <span style={{ color: '#94a3b8', fontStyle: 'italic', fontSize: '0.72rem' }}>select a question first</span>
  );

  const renderCell = (column: DesignColumn, row: DesignRow, rowIndex: number) => {
    const q = rowQuestion(row);

    switch (column.render) {
      case 'SERIAL':
        return <span style={{ color: '#475569', fontWeight: 500 }}>{rowIndex + 1}</span>;

      case 'QUESTION': {
        const isMissing = missingQuestionKeys.has(row.key);
        const isDuplicate = duplicateRowKeys.has(row.key);
        return (
          <div className="flex flex-column gap-1">
            <Dropdown
              value={row.questionId ?? null}
              options={questionDropdownOptions}
              onChange={(e) => pickRowQuestion(row.key, e.value)}
              filter
              showClear
              placeholder="Select question"
              className={`w-full${isMissing || isDuplicate ? ' p-invalid' : ''}`}
              style={{ fontSize: '0.75rem' }}
              emptyMessage="No questions"
            />
            {isMissing && (
              <small className="p-error">Question is required.</small>
            )}
            {!isMissing && isDuplicate && (
              <small className="p-error">This question is already used in another row here.</small>
            )}
            {/* Sub-questions listed under the question */}
            {q?.hasSubQuestion && q.subQuestions.length > 0 && (
              <div style={{ paddingLeft: '0.6rem', marginTop: '0.15rem' }}>
                {q.subQuestions.map((sub) => (
                  <div key={sub.id} style={{ fontSize: '0.7rem', color: '#64748b' }}>• {sub.title}</div>
                ))}
              </div>
            )}
          </div>
        );
      }

      case 'OPTION': {
        if (!q) return needQuestion;
        if (q.options.length === 0) {
          return <span style={{ color: '#94a3b8', fontStyle: 'italic', fontSize: '0.72rem' }}>no options</span>;
        }
        return (
          <div className="flex flex-column gap-1">
            {q.options.map((o) => (
              <span key={o.id} style={{ fontSize: '0.72rem', color: '#475569' }}>• {o.label}</span>
            ))}
          </div>
        );
      }

      case 'AQL_LIMIT': {
        if (!q) return needQuestion;
        // A row-level override (set via Row Settings) wins over the question
        // master's default AQL limit.
        const limit = row.aqlLimit || q.aqlLimit;
        return <span style={{ color: '#475569', fontWeight: 500 }}>{limit ? parseFloat(limit).toString() : '-'}</span>;
      }

      case 'RESPONSE':
        return <ResponseInput name={`resp_${column.key}_${row.key}`} />;

      case 'ANSWER':
      default: {
        if (!q) return needQuestion;
        return (
          <div className="flex flex-column gap-2">
            {/* Main question's answer */}
            <AnswerInput
              answerType={q.answerType}
              hasTextBox={q.hasTextBox}
              hasMultipleTextBox={q.hasMultipleTextBox}
              masterType={q.masterType}
            />
            {/* Each sub-question's own answer box */}
            {q.hasSubQuestion &&
              q.subQuestions.map((sub) => (
                <AnswerInput
                  key={sub.id}
                  answerType={sub.answerType}
                  hasTextBox={sub.hasTextBox}
                  hasMultipleTextBox={sub.hasMultipleTextBox}
                  placeholder={sub.title}
                />
              ))}
          </div>
        );
      }
    }
  };

  return (
    <div className="snip-table-wrap">
      <table className="snip-table">
        <thead>
          <tr>
            {columns.map((c, ci) => (
              <th key={c.key} className="snip-col-header" style={{ width: columnWidthStyle(c.width) }}>
                <div className="snip-col-header-top">
                  <InputText
                    value={c.header}
                    onChange={(e) => patchColumn(c.key, { header: e.target.value })}
                    placeholder="Header"
                    className="snip-col-header-input"
                  />
                  <Button
                    icon="pi pi-times" rounded text severity="secondary" size="small"
                    onClick={() => removeColumn(c.key)} type="button"
                    tooltip="Remove column" tooltipOptions={{ position: 'top' }}
                    className="snip-col-remove-btn"
                  />
                </div>

                {/* Type picker */}
                <Dropdown
                  value={c.render}
                  options={typeOptions}
                  onChange={(e) => patchColumn(c.key, { render: e.value })}
                  className="w-full snip-col-type-dropdown"
                />

                {/* Reorder + width */}
                <div className="snip-col-toolbar">
                  <Button
                    icon="pi pi-angle-left" rounded text severity="secondary" size="small"
                    disabled={ci === 0} onClick={() => moveColumn(c.key, -1)} type="button"
                    tooltip="Move left" tooltipOptions={{ position: 'top' }}
                    className="snip-col-move-btn"
                  />
                  <Button
                    icon="pi pi-angle-right" rounded text severity="secondary" size="small"
                    disabled={ci === columns.length - 1} onClick={() => moveColumn(c.key, 1)} type="button"
                    tooltip="Move right" tooltipOptions={{ position: 'top' }}
                    className="snip-col-move-btn"
                  />
                  <InputText
                    value={widthToNumber(c.width)}
                    onChange={(e) => patchColumn(c.key, { width: numberToWidth(e.target.value) })}
                    placeholder="8"
                    tooltip="Column width (e.g. 8)"
                    tooltipOptions={{ position: 'top' }}
                    className="snip-col-width-input"
                    inputMode="decimal"
                  />
                </div>
              </th>
            ))}

            <th className="snip-add-col-cell">
              <div className="snip-add-col-cell-inner">
                <Button
                  icon="pi pi-file-plus" rounded text raised severity="success" size="small"
                  onClick={addColumn} type="button"
                  tooltip="Add column" tooltipOptions={{ position: 'top' }}
                  className="snip-add-col-btn"
                />
              </div>
            </th>
          </tr>
        </thead>
        <tbody>
          {columns.length === 0 ? (
            <tr>
              <td className="snip-empty-state">
                Click the <strong>+</strong> to add your first column.
              </td>
            </tr>
          ) : rows.length === 0 ? (
            <tr>
              <td colSpan={columns.length + 1} className="snip-empty-state">
                No rows yet. Click <strong>Add Row</strong> below.
              </td>
            </tr>
          ) : (
            rows.map((row, ri) => (
              <tr
                key={row.key}
                {...rowDrag.getItemProps(ri)}
                className={rowDrag.dragOverIndex === ri ? 'snip-row-drag-over' : undefined}
                style={{ opacity: rowDrag.draggingIndex === ri ? 0.5 : 1 }}
              >
                {columns.map((c) => (
                  <td key={c.key} className="snip-cell" style={{ width: columnWidthStyle(c.width) }}>
                    {renderCell(c, row, ri)}
                  </td>
                ))}
                <td className="snip-cell snip-row-actions-cell">
                  <div className="snip-row-actions">
                    {row.isDeclaration && (
                      <Tag value="Decl" severity="info" className="snip-row-declaration-tag" />
                    )}
                    <span {...rowDrag.getHandleProps(ri)} title="Drag to reorder" className="snip-row-drag-handle">
                      <i className="pi pi-arrows-alt" />
                    </span>
                    <Button
                      icon="pi pi-cog" rounded text severity="secondary" size="small"
                      onClick={(e) => { setSettingsRowKey(row.key); settingsOp.current?.show(e, e.currentTarget as HTMLElement); }}
                      type="button" tooltip="Row settings" tooltipOptions={{ position: 'top' }}
                      className="snip-row-action-btn"
                    />
                    <Button
                      icon="pi pi-trash" rounded text severity="danger" size="small"
                      onClick={() => removeRow(row.key)} type="button"
                      tooltip="Remove row" tooltipOptions={{ position: 'top' }}
                      className="snip-row-action-btn"
                    />
                  </div>
                </td>
              </tr>
            ))
          )}
        </tbody>
      </table>

      {/* Per-row settings popover — mirrors the Stage Question Mapping attributes */}
      <OverlayPanel ref={settingsOp} dismissable style={{ width: 300 }}>
        {(() => {
          const row = rows.find((r) => r.key === settingsRowKey);
          if (!row) return null;
          const patch = (fields: Partial<DesignRow>) => patchRow(row.key, fields);
          const noneApply =
            !showShowOnGrid && !showSapField && !showIsEditable && !showDeclaration && !showCustomAnswers && !showAqlLimit;
          return (
            <div className="flex flex-column gap-3" style={{ padding: '0.25rem' }}>
              <div className="flex align-items-center justify-content-between">
                <div className="text-sm font-semibold">Row Settings</div>
                <Button
                  icon="pi pi-times" rounded text severity="secondary" size="small"
                  onClick={() => settingsOp.current?.hide()} type="button"
                  tooltip="Close" tooltipOptions={{ position: 'top' }}
                  className="snip-col-remove-btn"
                />
              </div>

              {showShowOnGrid && (
                <div className="flex align-items-center justify-content-between">
                  <label className="text-sm">Show on Grid</label>
                  <InputSwitch checked={!!row.showOnGrid} onChange={(e) => patch({ showOnGrid: e.value })} />
                </div>
              )}

              {showSapField && (
                <div className="flex flex-column gap-1">
                  <label className="text-sm">SAP Answer Field</label>
                  <Dropdown
                    value={row.sapFieldId ?? null}
                    options={sapFieldOptions}
                    onChange={(e) => patch({ sapFieldId: e.value })}
                    placeholder="Select SAP Field" filter showClear className="w-full"
                  />
                </div>
              )}

              {showIsEditable && (
                <div className="flex align-items-center justify-content-between">
                  <label className="text-sm">Is Editable</label>
                  <InputSwitch checked={row.isEditable ?? true} onChange={(e) => patch({ isEditable: e.value })} />
                </div>
              )}

              {showDeclaration && (
                <div className="flex align-items-center justify-content-between">
                  <label className="text-sm">Declaration Question</label>
                  <InputSwitch checked={!!row.isDeclaration} onChange={(e) => patch({ isDeclaration: e.value })} />
                </div>
              )}

              {showCustomAnswers && (
                <div className="flex flex-column gap-1">
                  <label className="text-sm">Custom Answer Type</label>
                  <Dropdown
                    value={row.customAnswer ?? null}
                    options={customAnswerOptions}
                    onChange={(e) => patch({ customAnswer: e.value })}
                    placeholder="Select Custom Answer" showClear className="w-full"
                  />
                </div>
              )}

              {showAqlLimit && (
                <div className="flex flex-column gap-1">
                  <label className="text-sm">AQL Limit</label>
                  <InputText
                    value={row.aqlLimit ?? ''}
                    onChange={(e) => patch({ aqlLimit: e.target.value })}
                    placeholder="e.g. 0.5" className="w-full"
                  />
                </div>
              )}

              {noneApply && (
                <div className="text-500 text-xs">
                  No extra attributes apply for this stage / format.
                </div>
              )}
            </div>
          );
        })()}
      </OverlayPanel>

      {columns.length > 0 && (
        <Button
          icon="pi pi-list"
          rounded raised
          onClick={addRow}
          type="button"
          className="mt-3 mb-2 snip-add-btn snip-add-btn--row"
          aria-label="Add Row"
          tooltip="Add Row"
          tooltipOptions={{ position: 'top' }}
        />
      )}
    </div>
  );
};
