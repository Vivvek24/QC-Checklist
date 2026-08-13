/**
 * Business Unit master API calls.
 * Maps to backend: /api/v1/masters/business-units
 */

import { createMasterApi } from './createMasterApi';
import type {
  BusinessUnit,
  BusinessUnitListParams,
  CreateBusinessUnitRequest,
  UpdateBusinessUnitRequest,
} from '../models/BusinessUnit';

export const businessUnitApi = createMasterApi<
  BusinessUnit,
  CreateBusinessUnitRequest,
  UpdateBusinessUnitRequest,
  BusinessUnitListParams
>('/masters/business-units', 'items');
