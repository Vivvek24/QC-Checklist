/**
 * TanStack Query hooks for the Published Darwin AD Service test harness.
 *
 * Each hook is a mutation so calls are triggered explicitly from the UI (this
 * is a test harness, not a live data feed). The `apiKey` is threaded through
 * from the page-level input.
 */

import { useMutation } from '@tanstack/react-query';

import { publishedDarwinAdApi } from '../api/publishedDarwinAdApi';

export const usePublishedGetEmployees = () => {
  return useMutation({
    mutationFn: (vars: { apiKey: string; status?: string }) =>
      publishedDarwinAdApi.getEmployees(vars.apiKey, vars.status),
  });
};

export const usePublishedGetSelectedEmployees = () => {
  return useMutation({
    mutationFn: (vars: { apiKey: string; employeeIds: string }) =>
      publishedDarwinAdApi.getSelectedEmployees(vars.apiKey, vars.employeeIds),
  });
};

export const usePublishedGetEmployeeDetails = () => {
  return useMutation({
    mutationFn: (vars: { apiKey: string; employeeIds: string }) =>
      publishedDarwinAdApi.getEmployeeDetails(vars.apiKey, vars.employeeIds),
  });
};

export const usePublishedGetHierarchy = () => {
  return useMutation({
    mutationFn: (vars: { apiKey: string }) => publishedDarwinAdApi.getHierarchyData(vars.apiKey),
  });
};

export const usePublishedValidateCredentials = () => {
  return useMutation({
    mutationFn: (vars: { apiKey: string; employeeId: string; password: string }) =>
      publishedDarwinAdApi.validateCredentials(vars.apiKey, vars.employeeId, vars.password),
  });
};
