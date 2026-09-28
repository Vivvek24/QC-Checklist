/**
 * Read-only shapes returned by GET /qc-checklist/preview, as consumed by
 * CreateRequestPage and the Snip grid components it renders (AQLSnip,
 * ReconcilationSheetSnip, TemplateDrivenSnip, ApprovalSnip).
 *
 * Deliberately separate from template-studio/models/Preview.ts — that one
 * is Template Studio's own read model for the same endpoint, and the two
 * features evolve independently even though they share a backend response
 * shape today.
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
  sub_questions: QuestionAnswerPreview[];
  options: { id: number; label: string }[];
  response_options: { id: number; label: string }[];
}

export interface ApprovalLabelPreview {
  approval_label_id: number;
  label: string;
}

export interface SectionPreview {
  section_id: number;
  section_name: string;
  questions: QuestionAnswerPreview[];
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
  approval_labels: ApprovalLabelPreview[];
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
