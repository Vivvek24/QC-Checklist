import type { MasterListParams, MasterRecord } from './common';
export interface ValidationType extends MasterRecord { name: string; }
export interface CreateValidationTypeRequest { name: string; is_active: boolean; }
export type UpdateValidationTypeRequest = Partial<CreateValidationTypeRequest>;
export type ValidationTypeListParams = MasterListParams;
