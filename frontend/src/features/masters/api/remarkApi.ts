import { createMasterApi } from './createMasterApi';
import type { Remark, RemarkListParams, CreateRemarkRequest, UpdateRemarkRequest } from '../models/Remark';
export const remarkApi = createMasterApi<Remark, CreateRemarkRequest, UpdateRemarkRequest, RemarkListParams>('/masters/remarks', 'items');
