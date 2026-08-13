import { stageApi } from '../api/stageApi';
import { createMasterHooks } from './createMasterHooks';
import { MASTER_KEYS } from './masterQueryKeys';
import type { Stage, StageListParams, CreateStageRequest, UpdateStageRequest } from '../models/Stage';

const hooks = createMasterHooks<Stage, CreateStageRequest, UpdateStageRequest, StageListParams>(stageApi, MASTER_KEYS.stages);

export const useStages = hooks.useList;
export const useCreateStage = hooks.useCreate;
export const useUpdateStage = hooks.useUpdate;
export const useDeleteStage = hooks.useDelete;
