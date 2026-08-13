/**
 * Unit master types.
 * Mirrors backend UnitResponse / UnitCreate / UnitUpdate.
 */

import type { MasterListParams, MasterRecord } from './common';

export interface Unit extends MasterRecord {
  name: string;
  business_unit_id: number;
}

export interface CreateUnitRequest {
  name: string;
  business_unit_id: number;
  is_active: boolean;
}

export type UpdateUnitRequest = Partial<CreateUnitRequest>;

export type UnitListParams = MasterListParams;
