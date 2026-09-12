/**
 * Darwinbox Service API calls.
 * Maps to backend: /api/v1/services/darwinbox/*
 *
 * Endpoints:
 *   GET  /health                      - Service reachability + per-dataset configured flags
 *   GET  /employees?dataset=...        - Fetch raw employee master (no persistence)
 *   GET  /stored?status=...&skip=&limit= - List employees synced into the DB
 *   POST /sync?scope=...               - Fetch dataset(s) and upsert into the DB
 */

import { apiClient } from '@shared/services/apiClient';

export type DarwinboxDataset = 'active' | 'inactive';
export type DarwinboxSyncScope = 'active' | 'inactive' | 'all';

// The Darwinbox master API returns ~16k records and can take several minutes.
// Override the default axios timeout for these long-running calls so the browser
// waits for the backend to finish instead of erroring out early.
const LONG_TIMEOUT_MS = 600000; // 10 minutes

export interface DarwinboxHealthResponse {
  service: string;
  active_configured: boolean;
  inactive_configured: boolean;
  base_url: string;
  status: string;
  status_code?: number;
  url?: string;
  error?: string;
}

export interface DarwinboxFetchResponse {
  dataset: DarwinboxDataset;
  status: number;
  message: string;
  count: number;
  employee_data: Array<Record<string, unknown>>;
}

export interface SyncEmployeesResponse {
  datasets: string[];
  total: number;
  created: number;
  updated: number;
  failed: number;
  message: string;
}

export interface DarwinboxEmployee {
  id: string;
  employee_id: string;
  full_name: string;
  first_name: string;
  middle_name: string;
  last_name: string;
  company_email_id: string;
  employee_status: string;
  designation_title: string;
  job_level: string;
  role: string;
  department: string;
  business_unit: string;
  division: string;
  group_company: string;
  catalyst_additional_department: string;
  departments_hierarchy: string;
  cost_center_id: string;
  cost_center: string;
  office_mobile_no: string;
  extension_mobile_no: string;
  personal_mobile_no: string;
  current_address: string;
  current_country: string;
  current_location: string;
  office_location: string;
  custom_location: string;
  office_state: string;
  office_city: string;
  direct_manager_employee_id: string;
  direct_manager_name: string;
  direct_manager_email: string;
  territory_code: string;
  territory_name: string;
  bank_pan: string;
  date_of_birth: string;
  gender: string;
  date_of_exit: string;
  created_by: string;
  created_date: string;
  modified_by: string;
  modified_date: string;
}

export interface DarwinboxEmployeeListResponse {
  employees: DarwinboxEmployee[];
  total: number;
  skip: number;
  limit: number;
}

export interface ListStoredParams {
  skip?: number;
  limit?: number;
  status?: string;
  search?: string;
}

export const darwinboxApi = {
  healthCheck: async (): Promise<DarwinboxHealthResponse> => {
    const { data } = await apiClient.get<DarwinboxHealthResponse>(
      '/services/darwinbox/health'
    );
    return data;
  },

  getEmployees: async (
    dataset: DarwinboxDataset
  ): Promise<DarwinboxFetchResponse> => {
    const { data } = await apiClient.get<DarwinboxFetchResponse>(
      '/services/darwinbox/employees',
      { params: { dataset }, timeout: LONG_TIMEOUT_MS }
    );
    return data;
  },

  listStored: async (
    params: ListStoredParams = {}
  ): Promise<DarwinboxEmployeeListResponse> => {
    const { data } = await apiClient.get<DarwinboxEmployeeListResponse>(
      '/services/darwinbox/stored',
      { params }
    );
    return data;
  },

  sync: async (scope: DarwinboxSyncScope): Promise<SyncEmployeesResponse> => {
    const { data } = await apiClient.post<SyncEmployeesResponse>(
      '/services/darwinbox/sync',
      null,
      { params: { scope }, timeout: LONG_TIMEOUT_MS }
    );
    return data;
  },
};
