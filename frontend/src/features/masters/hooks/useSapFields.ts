import { sapFieldApi } from '../api/sapFieldApi';
import { createMasterHooks } from './createMasterHooks';
import { MASTER_KEYS } from './masterQueryKeys';
import type { SapField, SapFieldListParams, CreateSapFieldRequest, UpdateSapFieldRequest } from '../models/SapField';
const h = createMasterHooks<SapField, CreateSapFieldRequest, UpdateSapFieldRequest, SapFieldListParams>(sapFieldApi, MASTER_KEYS.sapFields);
export const useSapFields = h.useList;
export const useCreateSapField = h.useCreate;
export const useUpdateSapField = h.useUpdate;
export const useDeleteSapField = h.useDelete;
