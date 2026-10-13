/**
 * TanStack Query hooks for the SAP Integration service.
 */

import { useMutation, useQuery } from '@tanstack/react-query';
import { sapApi } from '../api/sapApi';

export const useSapHealth = () =>
  useQuery({
    queryKey: ['sap', 'health'],
    queryFn: () => sapApi.healthCheck(),
    staleTime: 10_000,
    retry: 1,
  });

export const useSapQcChecklist = () =>
  useMutation({
    mutationFn: (inspLot: string) => sapApi.getQcChecklist(inspLot),
  });
