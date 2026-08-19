import type { MasterListParams, MasterRecord } from './common';

export interface TestMaster extends MasterRecord {
  test_name: string;
  sample_description: string;
  sample_qty: number;
  product_id: number;
}

export interface CreateTestMasterRequest {
  test_name: string;
  sample_description: string;
  sample_qty: number;
  product_id: number;
  is_active: boolean;
}

export type UpdateTestMasterRequest = Partial<CreateTestMasterRequest>;

export interface TestMasterListParams extends MasterListParams {
  product_id?: number;
}
