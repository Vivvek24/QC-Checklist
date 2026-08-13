import { validationTypeApi } from '../api/validationTypeApi';
import { createMasterHooks } from './createMasterHooks';
import { MASTER_KEYS } from './masterQueryKeys';
import type { ValidationType, ValidationTypeListParams, CreateValidationTypeRequest, UpdateValidationTypeRequest } from '../models/ValidationType';
const h = createMasterHooks<ValidationType, CreateValidationTypeRequest, UpdateValidationTypeRequest, ValidationTypeListParams>(validationTypeApi, MASTER_KEYS.validationTypes);
export const useValidationTypes = h.useList;
export const useCreateValidationType = h.useCreate;
export const useUpdateValidationType = h.useUpdate;
export const useDeleteValidationType = h.useDelete;
