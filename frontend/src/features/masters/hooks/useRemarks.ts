import { remarkApi } from '../api/remarkApi';
import { createMasterHooks } from './createMasterHooks';
import { MASTER_KEYS } from './masterQueryKeys';
import type { Remark, RemarkListParams, CreateRemarkRequest, UpdateRemarkRequest } from '../models/Remark';
const h = createMasterHooks<Remark, CreateRemarkRequest, UpdateRemarkRequest, RemarkListParams>(remarkApi, MASTER_KEYS.remarks);
export const useRemarks = h.useList;
export const useCreateRemark = h.useCreate;
export const useUpdateRemark = h.useUpdate;
export const useDeleteRemark = h.useDelete;
