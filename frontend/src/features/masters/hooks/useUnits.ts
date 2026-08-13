/**
 * Unit master query hooks.
 */

import { unitApi } from '../api/unitApi';
import { createMasterHooks } from './createMasterHooks';
import { MASTER_KEYS } from './masterQueryKeys';
import type {
  Unit,
  UnitListParams,
  CreateUnitRequest,
  UpdateUnitRequest,
} from '../models/Unit';

const hooks = createMasterHooks<
  Unit,
  CreateUnitRequest,
  UpdateUnitRequest,
  UnitListParams
>(unitApi, MASTER_KEYS.units);

export const useUnits = hooks.useList;
export const useCreateUnit = hooks.useCreate;
export const useUpdateUnit = hooks.useUpdate;
export const useDeleteUnit = hooks.useDelete;
