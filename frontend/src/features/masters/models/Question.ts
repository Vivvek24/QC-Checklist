import type { MasterListParams, MasterRecord } from './common';

export type AnswerType =
  | 'Text Box'
  | 'None'
  | 'Dropdown (single select)'
  | 'Dropdown (multi select)'
  | 'Date & Time'
  | 'Masters';

export const ANSWER_TYPE_OPTIONS: { label: string; value: AnswerType }[] = [
  { label: 'None', value: 'None' },
  { label: 'Text Box', value: 'Text Box' },
  { label: 'Dropdown (single select)', value: 'Dropdown (single select)' },
  { label: 'Dropdown (multi select)', value: 'Dropdown (multi select)' },
  { label: 'Date & Time', value: 'Date & Time' },
  { label: 'Masters', value: 'Masters' },
];

export interface Question extends MasterRecord {
  title: string;
  answer_type: AnswerType;
  has_text_box: boolean;
  has_multiple_text_box: boolean;
  has_sub_question: boolean;
  is_validation_required: boolean;
  has_response_option: boolean;
  allow_multiple_input: boolean;
  has_associated_master: boolean;
  is_calculated: boolean;
  validation_type_id: number | null;
  master_type: string | null;
  parent_question_id: number | null;
  sub_question_ids: number[];
}

export interface CreateQuestionRequest {
  title: string;
  answer_type: AnswerType;
  has_text_box: boolean;
  has_multiple_text_box: boolean;
  has_sub_question: boolean;
  is_validation_required: boolean;
  has_response_option: boolean;
  allow_multiple_input: boolean;
  has_associated_master: boolean;
  is_calculated: boolean;
  is_active: boolean;
  validation_type_id: number | null;
  master_type: string | null;
  parent_question_id: number | null;
  sub_question_ids: number[];
}

export type UpdateQuestionRequest = Partial<CreateQuestionRequest>;
export type QuestionListParams = MasterListParams;
