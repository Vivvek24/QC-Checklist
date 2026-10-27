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
  /** For answer_type "Masters": which master this question draws from (e.g. "Product Master"). */
  master_type?: string | null;
  has_text_box: boolean;
  has_multiple_text_box: boolean;
  has_sub_question?: boolean;
  /** When false, this question's answer field is locked (read-only) even for a
   * fillable stage — configured per question in Template Studio. */
  is_editable?: boolean;
  aql_limit?: string;
  /** SAP field this question maps to (e.g. "INSP_LOT"); matched against SAP
   * QC_Checklist response keys to auto-fill answers. Null/undefined when unmapped. */
  sap_field_name?: string | null;
  /** True when this question carries its own approval labels. */
  is_approvable?: boolean;
  /** True when picking a product auto-fills this question's answer with the
   * product's storage conditions. */
  has_associated_master?: boolean;
  /** True when the "+ Add" helper button runs the calculated-answer flow. */
  is_calculated?: boolean;
  /** Custom answer behaviour (e.g. "Calculate_SampleConsumed"). */
  custom_answers?: string | null;
  options: { id: number; label: string }[];
  /** Response options for the RESPONSE_QUESTION_OPTION column dropdown. */
  response_options?: { id: number; label: string }[];
  /** Child questions shown nested under this one (read-only display). */
  sub_questions?: QuestionAnswerPreview[];
  /** Approval labels configured for this question (empty/undefined unless approvable). */
  approval_labels?: { approval_label_id: number; label: string; role_ids?: number[] }[];
  /** Set only for auto-generated per-test rows (TEST_TITLE / SAMPLE_VIAL
   * columns). Absent for normal configured questions. */
  test_title?: string;
  sample_vails?: string;
}

export interface TemplateSubAnswer {
  question_id: number;
  textbox_value: string;
  question_option_id: number | null;
  response_answer: string;
}

export interface TemplateAnswer {
  stage_question_mapping_id: number;
  question_id: number;
  textbox_value: string;
  question_option_id: number | null;
  /** Chosen response option id (RESPONSE_QUESTION_OPTION column). */
  response_question_option_id: number | null;
  /** Chosen product id when answer_type is "Masters" (Product Master). */
  product_id: number | null;
  /** Picked date-time (ISO) when answer_type is "Date & Time". */
  date_time: string | null;
  response_answer: string;
  /** True when this (calculated) answer's values are held in helper boxes. */
  has_helper?: boolean;
  /** Running total of a calculated question's accumulated values. */
  answer_total_vails?: number;
  helpers: string[];
  /** Answers for this question's sub-questions (if any). */
  sub_answers: TemplateSubAnswer[];
}

export interface TemplateDrivenSnipHandle {
  validate: () => boolean;
  getAnswers: () => TemplateAnswer[];
  /** Per-question approval remark picks (empty unless the stage has approvable
   * questions and the user acted on them). */
  getQuestionApprovals?: () => import('../api/qcChecklistApi').QuestionApprovalInput[];
}
