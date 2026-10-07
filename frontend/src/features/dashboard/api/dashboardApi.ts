/**
 * Dashboard API — reads the QC Checklist dashboard payload (pending + approved
 * requests and the total count) for a date range. Backed by the
 * GET /qc-checklist/dashboard endpoint.
 */

import { apiClient } from '@shared/services/apiClient';
import { formatDate, type DashboardResponse } from '../models/DashboardTypes';

export const dashboardApi = {
  /** Fetch the dashboard rows + total for a [from, to) date window. */
  getDashboard: async (from: Date, to: Date): Promise<DashboardResponse> => {
    const { data } = await apiClient.get<DashboardResponse>('/qc-checklist/dashboard', {
      params: { from_date: formatDate(from), to_date: formatDate(to) },
    });
    return data;
  },
};
