/**
 * Unit master API calls.
 * Maps to backend: /api/v1/masters/units
 */

import { createMasterApi } from './createMasterApi';
import type {
  Unit,
  UnitListParams,
  CreateUnitRequest,
  UpdateUnitRequest,
} from '../models/Unit';

export const unitApi = createMasterApi<
  Unit,
  CreateUnitRequest,
  UpdateUnitRequest,
  UnitListParams
>('/masters/units', 'items');
