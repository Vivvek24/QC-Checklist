/**
 * Read-only shapes returned by GET /qc-checklist/preview.
 * Mirrors the interfaces used in qc-checklist/CreateRequestPage — kept local so
 * this feature is self-contained. We only READ this data.
 */

export interface QuestionAnswerPreview {
  stage_question_mapping_id: number;
  question_id: number;
  question_title: string;
  serial_number: number;
  section_id: number | null;
  section_name: string | null;
  show_on_grid: boolean;
  answer_type: string;
  has_text_box: boolean;
  has_multiple_text_box: boolean;
  has_sub_question: boolean;
  is_declaration_question: boolean;
  aql_limit: string;
  master_type?: string | null;
  /** Edit-only mapping attributes — carried so Template Studio can hydrate
   * its design canvas from the preview call alone (no separate
   * stage-question-mappings fetch). */
  sap_field_id: number | null;
  is_editable: boolean;
  custom_answers: string | null;
  sub_questions: QuestionAnswerPreview[];
  options: { id: number; label: string }[];
  response_options: { id: number; label: string }[];
}

/** A single Template Studio column, as read for rendering (not editing). */
export interface ColumnPreview {
  id: number;
  header: string;
  column_type: string;
  display_order: number;
  width: string | null;
  is_required: boolean;
}

export interface SectionPreview {
  section_id: number;
  section_name: string;
  questions: QuestionAnswerPreview[];
  columns: ColumnPreview[];
}

export interface ChecklistStagePreview {
  format_stage_mapping_id: number;
  stage_id: number;
  stage_name: string;
  is_approvable: boolean;
  has_section: boolean;
  status: string;
  questions: QuestionAnswerPreview[];
  sections: SectionPreview[];
  approval_labels: { approval_label_id: number; label: string }[];
  columns: ColumnPreview[];
}

export interface ChecklistPreview {
  format_id: number;
  format_name: string;
  format_no: string;
  format_type: string;
  has_declaration_question: boolean;
  unit_name: string;
  stages: ChecklistStagePreview[];
}
