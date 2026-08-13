/**
 * Business Unit master query hooks.
 */

import { businessUnitApi } from '../api/businessUnitApi';
import { createMasterHooks } from './createMasterHooks';
import { MASTER_KEYS } from './masterQueryKeys';
import type {
  BusinessUnit,
  BusinessUnitListParams,
  CreateBusinessUnitRequest,
  UpdateBusinessUnitRequest,
} from '../models/BusinessUnit';

const hooks = createMasterHooks<
  BusinessUnit,
  CreateBusinessUnitRequest,
  UpdateBusinessUnitRequest,
  BusinessUnitListParams
>(businessUnitApi, MASTER_KEYS.businessUnits);

export const useBusinessUnits = hooks.useList;
export const useCreateBusinessUnit = hooks.useCreate;
export const useUpdateBusinessUnit = hooks.useUpdate;
export const useDeleteBusinessUnit = hooks.useDelete;
