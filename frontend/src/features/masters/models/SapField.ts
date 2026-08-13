import type { MasterListParams, MasterRecord } from './common';
export interface SapField extends MasterRecord { field_name: string; }
export interface CreateSapFieldRequest { field_name: string; is_active: boolean; }
export type UpdateSapFieldRequest = Partial<CreateSapFieldRequest>;
export type SapFieldListParams = MasterListParams;
