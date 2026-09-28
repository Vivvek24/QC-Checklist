/**
 * DesignSpec — the composed layout for a format's checklist, built in the
 * Design tab. A format's canvas is a list of freely-added data tables; each
 * table has a title and a list of columns; each column declares what it renders.
 *
 * This is a self-contained config. It does NOT modify any masters — a QUESTION
 * column merely references an existing question master by id.
 */

/**
 * The type of a column, chosen from a fixed enum. A column's cell in each row
 * renders according to this type:
 *  - SERIAL    → auto Sr No (row index)
 *  - QUESTION  → a question picked from the question master (the row's question)
 *  - OPTION    → select option (auto-populated from the row's picked question)
 *  - ANSWER    → enter answer; branches on the question's answer_type
 *  - RESPONSE  → YES / NO / N-A radio group (Chromatographic response)
 *  - AQL_LIMIT → AQL limit (auto from the row's picked question)
 */
export type ColumnRender = 'SERIAL' | 'QUESTION' | 'OPTION' | 'ANSWER' | 'RESPONSE' | 'AQL_LIMIT';

export interface ColumnRenderMeta {
  render: ColumnRender;
  label: string;
  /** Suggested default header when this type is chosen. */
  defaultHeader: string;
}

export const COLUMN_RENDERS: ColumnRenderMeta[] = [
  { render: 'SERIAL', label: 'Sr No', defaultHeader: 'Sr No' },
  { render: 'QUESTION', label: 'Question', defaultHeader: 'Question' },
  { render: 'OPTION', label: 'Select Option', defaultHeader: 'Select Options' },
  { render: 'ANSWER', label: 'Enter Answer', defaultHeader: 'Enter Answer' },
  { render: 'RESPONSE', label: 'Yes / No / N-A', defaultHeader: 'Response' },
  { render: 'AQL_LIMIT', label: 'AQL Limit', defaultHeader: 'AQL Limit' },
];

const FALLBACK_RENDER: ColumnRenderMeta = {
  render: 'ANSWER',
  label: 'Enter Answer',
  defaultHeader: 'Enter Answer',
};

export const columnRenderMeta = (render: ColumnRender): ColumnRenderMeta =>
  COLUMN_RENDERS.find((c) => c.render === render) ?? FALLBACK_RENDER;

export interface DesignColumn {
  key: string;
  /** Column header text. */
  header: string;
  /** The column type. */
  render: ColumnRender;
  /** Optional CSS width. */
  width?: string;
  /** Validation: cell must be filled at fill time. */
  required?: boolean;
}

export interface DesignRow {
  key: string;
  /** The backing stage_question_mappings.id once loaded/saved. Absent = new row. */
  mappingId?: number;
  /** The question chosen for this row (via the Question column cell). */
  questionId?: number;
  questionTitle?: string;

  // ─── Per-row mapping attributes (mirror the Stage Question Mapping form) ───
  /** Show this question on the grid (Basic Details). */
  showOnGrid?: boolean;
  /** SAP answer field id (Basic Details + AQL). */
  sapFieldId?: number | null;
  /** Whether the answer is editable at fill time (Basic Details + AQL/Reconciliation). */
  isEditable?: boolean;
  /** Declaration question flag (when format.has_declaration_question). */
  isDeclaration?: boolean;
  /** Custom answer type (Reconciliation). */
  customAnswer?: string | null;
  /** Row-level AQL limit override (AQL format only). */
  aqlLimit?: string;
}

export interface DesignSection {
  key: string;
  /** The backing sections.id once loaded/saved. Absent = new section. */
  sectionId?: number;
  /** Section name, typed inline (created here, like Stage Question Mapping). */
  sectionName: string;
  columns: DesignColumn[];
  rows: DesignRow[];
}

export interface DesignStage {
  key: string;
  /** The selected stage — its format_stage_mapping id, stage id, and name. */
  stageFsmId: number | null;
  stageId: number | null;
  stageName: string;
  columns: DesignColumn[];
  rows: DesignRow[];
  /** Optional sections nested under this stage, each with its own table. */
  sections: DesignSection[];
  /**
   * Mirrors format_stage_mappings.has_section — whether this stage is
   * sectioned. Drives whether "Add Section" is available, matching the
   * Stage Question Mapping page's mutual exclusivity (direct rows vs
   * sections), and is persisted back via PATCH /masters/format-stage-mappings.
   */
  hasSection: boolean;
}

export interface DesignSpec {
  formatId: number;
  stages: DesignStage[];
  updatedAt: string;
}

let _seq = 0;
const rid = (p: string) => `${p}_${Date.now().toString(36)}_${(_seq++).toString(36)}`;
export const newStageKey = () => rid('stg');
export const newSectionKey = () => rid('sec');
export const newColumnKey = () => rid('col');
export const newRowKey = () => rid('row');

export const emptyStage = (): DesignStage => ({
  key: newStageKey(),
  stageFsmId: null,
  stageId: null,
  stageName: '',
  columns: [],
  rows: [],
  sections: [],
  hasSection: false,
});

export const emptySection = (): DesignSection => ({
  key: newSectionKey(),
  sectionName: '',
  columns: [],
  rows: [],
});
