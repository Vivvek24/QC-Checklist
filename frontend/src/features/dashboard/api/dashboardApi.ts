/**
 * Dashboard API — reads the QC Checklist dashboard payload (pending + approved
 * requests and the total count) for a date range. Backed by the
 * GET /qc-checklist/dashboard endpoint.
 */

import { apiClient } from '@shared/services/apiClient';
import { formatDate, type DashboardResponse } from '../models/DashboardTypes';

export const dashboardApi = {
  /** Fetch the dashboard rows + total for a [from, to) date window. Either
   * bound may be null ('All Time') — a null bound is simply omitted, and the
   * backend treats a missing bound as unbounded. */
  getDashboard: async (from: Date | null, to: Date | null): Promise<DashboardResponse> => {
    const params: Record<string, string> = {};
    if (from) params.from_date = formatDate(from);
    if (to) params.to_date = formatDate(to);
    const { data } = await apiClient.get<DashboardResponse>('/qc-checklist/dashboard', { params });
    return data;
  },
};
