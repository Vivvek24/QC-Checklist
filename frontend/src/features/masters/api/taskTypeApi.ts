/**
 * Task type master API calls.
 * Maps to backend: /api/v1/masters/task-types
 */

import { createMasterApi } from './createMasterApi';
import type {
  CreateTaskTypeRequest,
  TaskType,
  TaskTypeListParams,
  UpdateTaskTypeRequest,
} from '../models/TaskType';

export const taskTypeApi = createMasterApi<
  TaskType,
  CreateTaskTypeRequest,
  UpdateTaskTypeRequest,
  TaskTypeListParams
>('/masters/task-types', 'task_types');
