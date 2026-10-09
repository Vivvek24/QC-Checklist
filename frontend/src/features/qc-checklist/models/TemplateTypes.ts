/**
 * Shared shapes for the template-driven checklist grid components
 * (TemplateDrivenSnip and friends) — the row data they render and the ref
 * handle they expose to CreateRequestPage's submit/draft flow.
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
  has_sub_question?: boolean;
  /** When false, this question's answer field is locked (read-only) even for a
   * fillable stage — configured per question in Template Studio. */
  is_editable?: boolean;
  aql_limit?: string;
  options: { id: number; label: string }[];
  /** Child questions shown nested under this one (read-only display). */
  sub_questions?: QuestionAnswerPreview[];
}

export interface TemplateAnswer {
  stage_question_mapping_id: number;
  question_id: number;
  textbox_value: string;
  question_option_id: number | null;
  response_answer: string;
  helpers: string[];
}

export interface TemplateDrivenSnipHandle {
  validate: () => boolean;
  getAnswers: () => TemplateAnswer[];
}
