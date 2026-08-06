/**
 * Legislation master API calls.
 * Maps to backend: /api/v1/masters/legislations
 */

import { createMasterApi } from './createMasterApi';
import type {
  CreateLegislationRequest,
  Legislation,
  LegislationListParams,
  UpdateLegislationRequest,
} from '../models/Legislation';

export const legislationApi = createMasterApi<
  Legislation,
  CreateLegislationRequest,
  UpdateLegislationRequest,
  LegislationListParams
>('/masters/legislations', 'legislations');
