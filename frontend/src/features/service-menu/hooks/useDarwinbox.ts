/**
 * TanStack Query hooks for Darwinbox Service operations.
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

import {
  darwinboxApi,
  type DarwinboxDataset,
  type DarwinboxSyncScope,
  type ListStoredParams,
} from '../api/darwinboxApi';

export const useDarwinboxHealth = () => {
  return useQuery({
    queryKey: ['darwinbox', 'health'],
    queryFn: () => darwinboxApi.healthCheck(),
    staleTime: 10_000,
    retry: 1,
  });
};

export const useDarwinboxStored = (params: ListStoredParams) => {
  return useQuery({
    queryKey: ['darwinbox', 'stored', params],
    queryFn: () => darwinboxApi.listStored(params),
    staleTime: 5_000,
  });
};

export const useFetchDarwinboxEmployees = () => {
  return useMutation({
    mutationFn: (dataset: DarwinboxDataset) => darwinboxApi.getEmployees(dataset),
  });
};

export const useSyncDarwinbox = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (scope: DarwinboxSyncScope) => darwinboxApi.sync(scope),
    onSuccess: () => {
      // Refresh the stored list after a successful sync
      queryClient.invalidateQueries({ queryKey: ['darwinbox', 'stored'] });
    },
  });
};
