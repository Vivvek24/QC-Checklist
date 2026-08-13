/**
 * Business Unit master types.
 * Mirrors backend BusinessUnitResponse / BusinessUnitCreate / BusinessUnitUpdate.
 */

import type { MasterListParams, MasterRecord } from './common';

export interface BusinessUnit extends MasterRecord {
  name: string;
}

export interface CreateBusinessUnitRequest {
  name: string;
  is_active: boolean;
}

export type UpdateBusinessUnitRequest = Partial<CreateBusinessUnitRequest>;

export type BusinessUnitListParams = MasterListParams;
