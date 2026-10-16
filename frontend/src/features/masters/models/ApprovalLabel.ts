import type { MasterListParams, MasterRecord } from './common';

export interface ApprovalLabel extends MasterRecord {
  label: string;
  /** A label belongs to either a stage or a question (one set, the other null). */
  stage_id: number | null;
  question_id: number | null;
  role_ids: number[];
}

export interface CreateApprovalLabelRequest {
  label: string;
  stage_id?: number | null;
  question_id?: number | null;
  role_ids: number[];
  is_active: boolean;
}

export type UpdateApprovalLabelRequest = Partial<CreateApprovalLabelRequest>;

export interface ApprovalLabelListParams extends MasterListParams {
  stage_id?: number;
  question_id?: number;
}
