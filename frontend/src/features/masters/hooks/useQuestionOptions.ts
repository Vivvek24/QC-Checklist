import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { questionOptionApi } from '../api/questionOptionApi';
import type { CreateQuestionOptionRequest, UpdateQuestionOptionRequest } from '../models/QuestionOption';

const KEY = ['masters', 'question-options'];

export const useQuestionOptions = (questionId?: number) =>
  useQuery({
    queryKey: [...KEY, { question_id: questionId }],
    queryFn: () => questionOptionApi.list({ question_id: questionId }),
    enabled: !!questionId,
    staleTime: 30_000,
  });

export const useCreateQuestionOption = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (request: CreateQuestionOptionRequest) => questionOptionApi.create(request),
    onSuccess: () => qc.invalidateQueries({ queryKey: KEY }),
  });
};

export const useUpdateQuestionOption = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, request }: { id: string; request: UpdateQuestionOptionRequest }) =>
      questionOptionApi.update(id, request),
    onSuccess: () => qc.invalidateQueries({ queryKey: KEY }),
  });
};

export const useDeleteQuestionOption = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => questionOptionApi.remove(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: KEY }),
  });
};
