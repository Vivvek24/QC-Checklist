import type { MasterListParams, MasterRecord } from './common';

export interface Remark extends MasterRecord {
  remark: string;
  role_ids: number[];
}

export interface CreateRemarkRequest {
  remark: string;
  role_ids: number[];
  is_active: boolean;
}

export type UpdateRemarkRequest = Partial<CreateRemarkRequest>;
export type RemarkListParams = MasterListParams;
