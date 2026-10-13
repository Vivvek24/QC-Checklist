/**
 * SAP Integration Service API calls.
 * Maps to backend: /api/v1/services/sap/*
 *
 *   GET /health        - SAP reachability + config status
 *   GET /qc-checklist   - QC checklist lookup by inspection lot (I_INSP)
 */

import { apiClient } from '@shared/services/apiClient';

export interface SapHealthResponse {
  service: string;
  configured: boolean;
  base_url: string;
  status: string;
  status_code?: number;
  url: string;
  error?: string;
}

/** The parsed T_OUTPUT.item fields (all optional — SAP may omit some). */
export interface SapQcChecklistItem {
  INSP_LOT?: string;
  MATERIAL?: string;
  PLANT?: string;
  VEND_BATCH?: string;
  SAP_BATCH?: string;
  INSP_QTY?: string;
  UNIT?: string;
  KTEXTMAT?: string;
  VEND_NAME?: string;
  [key: string]: unknown;
}

export interface SapQcChecklistResponse {
  insp_lot: string;
  item: SapQcChecklistItem;
  raw_response: Record<string, unknown>;
}

export const sapApi = {
  healthCheck: async (): Promise<SapHealthResponse> => {
    const { data } = await apiClient.get<SapHealthResponse>('/services/sap/health');
    return data;
  },

  getQcChecklist: async (inspLot: string): Promise<SapQcChecklistResponse> => {
    const { data } = await apiClient.get<SapQcChecklistResponse>(
      '/services/sap/qc-checklist',
      { params: { I_INSP: inspLot } }
    );
    return data;
  },
};
