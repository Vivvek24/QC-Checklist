import type { MasterListParams, MasterRecord } from './common';

export interface Stage extends MasterRecord {
  stage_name: string;
}

export interface CreateStageRequest {
  stage_name: string;
  is_active: boolean;
}

export type UpdateStageRequest = Partial<CreateStageRequest>;
export type StageListParams = MasterListParams;
