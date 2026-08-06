/**
 * State master API calls.
 * Maps to backend: /api/v1/masters/states
 */

import { createMasterApi } from './createMasterApi';
import type {
  CreateStateRequest,
  State,
  StateListParams,
  UpdateStateRequest,
} from '../models/State';

export const stateApi = createMasterApi<
  State,
  CreateStateRequest,
  UpdateStateRequest,
  StateListParams
>('/masters/states', 'states');
