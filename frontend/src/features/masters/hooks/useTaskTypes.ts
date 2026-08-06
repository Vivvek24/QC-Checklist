/**
 * Task type master query hooks.
 *
 * Independent of the country/state hierarchy, so there are no dependent caches.
 */

import { taskTypeApi } from '../api/taskTypeApi';
import { createMasterHooks } from './createMasterHooks';
import { MASTER_KEYS } from './masterQueryKeys';
import type {
  CreateTaskTypeRequest,
  TaskType,
  TaskTypeListParams,
  UpdateTaskTypeRequest,
} from '../models/TaskType';

const hooks = createMasterHooks<
  TaskType,
  CreateTaskTypeRequest,
  UpdateTaskTypeRequest,
  TaskTypeListParams
>(taskTypeApi, MASTER_KEYS.taskTypes);

export const useTaskTypes = hooks.useList;
export const useCreateTaskType = hooks.useCreate;
export const useUpdateTaskType = hooks.useUpdate;
export const useDeleteTaskType = hooks.useDelete;
