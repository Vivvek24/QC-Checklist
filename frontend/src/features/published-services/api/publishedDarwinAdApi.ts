/**
 * Published Darwin AD Service API calls (drop-in / legacy contract).
 *
 * Maps to backend routes mounted at the app root:
 *   GET  /adintegratorservices/rest/v1/getemployees        (optional ?status=)
 *   POST /adintegratorservices/rest/v1/getselectedemployees (form: EmployeeIDs)
 *   POST /adintegratorservices/rest/v1/getemployeedetails   (form: EmployeeIDs)
 *   GET  /adintegratorservices/rest/v1/getHierarchyData
 *   POST /adintegratorservices/rest/v1/validatecredentials  (form: EmployeeId, Password)
 *
 * Auth is via the optional `X-API-Key` header (empty = open). These endpoints
 * are called directly (not through the JWT apiClient) so the test harness
 * exercises the exact contract an external application would.
 */

import { publishedApiClient, withApiKey } from '@shared/services/publishedApiClient';

const BASE = '/adintegratorservices/rest/v1';

export interface DarwinEmployeeRecord {
  first_name: string;
  last_name: string;
  employee_id: string;
  company_email_id: string;
  employee_status: string;
  [key: string]: unknown;
}

export interface EmployeeDataResponse {
  employeeData: DarwinEmployeeRecord[];
}

export interface HierarchyItem {
  split_role: string;
  role: string;
  designation_title: string;
  department: string;
  split_department: string;
  job_level: string;
  level: number;
}

export interface HierarchyResponse {
  hierarchy: HierarchyItem[];
}

export interface ValidateCredentialResponse {
  IsSuccess: boolean;
  Message: string;
  IsValidUser: boolean;
}

export const publishedDarwinAdApi = {
  getEmployees: async (
    apiKey: string,
    status?: string
  ): Promise<EmployeeDataResponse> => {
    const { data } = await publishedApiClient.get<EmployeeDataResponse>(
      `${BASE}/getemployees`,
      withApiKey(apiKey, {
        params: status?.trim() ? { status: status.trim() } : undefined,
      })
    );
    return data;
  },

  getSelectedEmployees: async (
    apiKey: string,
    employeeIds: string
  ): Promise<EmployeeDataResponse> => {
    const body = new URLSearchParams({ EmployeeIDs: employeeIds });
    const { data } = await publishedApiClient.post<EmployeeDataResponse>(
      `${BASE}/getselectedemployees`,
      body,
      withApiKey(apiKey)
    );
    return data;
  },

  getEmployeeDetails: async (
    apiKey: string,
    employeeIds: string
  ): Promise<EmployeeDataResponse> => {
    const body = new URLSearchParams({ EmployeeIDs: employeeIds });
    const { data } = await publishedApiClient.post<EmployeeDataResponse>(
      `${BASE}/getemployeedetails`,
      body,
      withApiKey(apiKey)
    );
    return data;
  },

  getHierarchyData: async (apiKey: string): Promise<HierarchyResponse> => {
    const { data } = await publishedApiClient.get<HierarchyResponse>(
      `${BASE}/getHierarchyData`,
      withApiKey(apiKey)
    );
    return data;
  },

  validateCredentials: async (
    apiKey: string,
    employeeId: string,
    password: string
  ): Promise<ValidateCredentialResponse> => {
    const body = new URLSearchParams({
      EmployeeId: employeeId,
      Password: password,
    });
    const { data } = await publishedApiClient.post<ValidateCredentialResponse>(
      `${BASE}/validatecredentials`,
      body,
      withApiKey(apiKey)
    );
    return data;
  },
};
