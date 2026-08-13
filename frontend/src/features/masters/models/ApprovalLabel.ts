import type { MasterListParams, MasterRecord } from './common';

export interface ApprovalLabel extends MasterRecord {
  label: string;
  stage_id: number;
  role_ids: number[];
}

export interface CreateApprovalLabelRequest {
  label: string;
  stage_id: number;
  role_ids: number[];
  is_active: boolean;
}

export type UpdateApprovalLabelRequest = Partial<CreateApprovalLabelRequest>;

export interface ApprovalLabelListParams extends MasterListParams {
  stage_id?: number;
}
