import { apiClient } from '@shared/services/apiClient';
import type {
  ApprovalLabel,
  ApprovalLabelListParams,
  CreateApprovalLabelRequest,
  UpdateApprovalLabelRequest,
} from '../models/ApprovalLabel';
import type { MasterPage } from '../models/common';

const BASE = '/masters/approval-labels';

export const approvalLabelApi = {
  list: async (params?: ApprovalLabelListParams): Promise<MasterPage<ApprovalLabel>> => {
    const { data } = await apiClient.get<{ items: ApprovalLabel[]; total: number; skip: number; limit: number }>(BASE, {
      params: { skip: 0, limit: 100, ...params },
    });
    return { items: data.items ?? [], total: data.total, skip: data.skip, limit: data.limit };
  },

  getById: async (id: string): Promise<ApprovalLabel> => {
    const { data } = await apiClient.get<ApprovalLabel>(`${BASE}/${id}`);
    return data;
  },

  create: async (request: CreateApprovalLabelRequest): Promise<ApprovalLabel> => {
    const { data } = await apiClient.post<ApprovalLabel>(BASE, request);
    return data;
  },

  update: async (id: string, request: UpdateApprovalLabelRequest): Promise<ApprovalLabel> => {
    const { data } = await apiClient.patch<ApprovalLabel>(`${BASE}/${id}`, request);
    return data;
  },

  remove: async (id: string): Promise<void> => {
    await apiClient.delete(`${BASE}/${id}`);
  },
};
