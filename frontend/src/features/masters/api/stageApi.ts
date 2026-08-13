import { createMasterApi } from './createMasterApi';
import type { Stage, StageListParams, CreateStageRequest, UpdateStageRequest } from '../models/Stage';

export const stageApi = createMasterApi<Stage, CreateStageRequest, UpdateStageRequest, StageListParams>(
  '/masters/stages', 'items'
);
