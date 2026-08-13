import type { MasterRecord } from './common';

export interface QuestionOption extends MasterRecord {
  option_title: string;
  is_response_option: boolean;
  question_id: number;
}

export interface CreateQuestionOptionRequest {
  option_title: string;
  is_response_option: boolean;
  question_id: number;
  is_active: boolean;
}

export type UpdateQuestionOptionRequest = Partial<CreateQuestionOptionRequest>;
