import { apiClient } from '@shared/services/apiClient';
import type { MasterPage } from '../models/common';
import type { QuestionOption, CreateQuestionOptionRequest, UpdateQuestionOptionRequest } from '../models/QuestionOption';

const BASE = '/masters/question-options';

export const questionOptionApi = {
  list: async (params?: { question_id?: number; skip?: number; limit?: number }): Promise<MasterPage<QuestionOption>> => {
    const { data } = await apiClient.get<{ items: QuestionOption[]; total: number; skip: number; limit: number }>(BASE, {
      params: { skip: 0, limit: 100, ...params },
    });
    return { items: data.items ?? [], total: data.total, skip: data.skip, limit: data.limit };
  },

  create: async (request: CreateQuestionOptionRequest): Promise<QuestionOption> => {
    const { data } = await apiClient.post<QuestionOption>(BASE, request);
    return data;
  },

  update: async (id: string, request: UpdateQuestionOptionRequest): Promise<QuestionOption> => {
    const { data } = await apiClient.patch<QuestionOption>(`${BASE}/${id}`, request);
    return data;
  },

  remove: async (id: string): Promise<void> => {
    await apiClient.delete(`${BASE}/${id}`);
  },
};
