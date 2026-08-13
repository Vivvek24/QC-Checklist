import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { approvalLabelApi } from '../api/approvalLabelApi';
import { MASTER_KEYS } from './masterQueryKeys';
import type {
  ApprovalLabelListParams,
  CreateApprovalLabelRequest,
  UpdateApprovalLabelRequest,
} from '../models/ApprovalLabel';

const KEY = MASTER_KEYS.approvalLabels;

export const useApprovalLabels = (params?: ApprovalLabelListParams) =>
  useQuery({
    queryKey: [...KEY, params ?? {}],
    queryFn: () => approvalLabelApi.list(params),
    staleTime: 30_000,
  });

export const useCreateApprovalLabel = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (request: CreateApprovalLabelRequest) => approvalLabelApi.create(request),
    onSuccess: () => qc.invalidateQueries({ queryKey: KEY }),
  });
};

export const useUpdateApprovalLabel = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, request }: { id: string; request: UpdateApprovalLabelRequest }) =>
      approvalLabelApi.update(id, request),
    onSuccess: () => qc.invalidateQueries({ queryKey: KEY }),
  });
};

export const useDeleteApprovalLabel = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => approvalLabelApi.remove(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: KEY }),
  });
};
