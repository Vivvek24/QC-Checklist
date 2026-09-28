/**
 * QC Checklist API — read the checklist structure for a format and submit a
 * stage's answers (submit or save-as-draft). Backed by
 * backend/src/api/v1/endpoints/qc_checklist/checklist_controller.py (preview
 * + submit-stage endpoints).
 */

import { apiClient } from '@shared/services/apiClient';
import type { ChecklistPreview } from '../models/ChecklistPreview';

/** One row's answer, as returned by any Snip grid's getAnswers(). Optional
 * fields cover shapes only ReconcilationSheetSnip currently produces. */
export interface SubmitStageAnswerInput {
  stage_question_mapping_id: number;
  question_id: number;
  textbox_value: string;
  question_option_id: number | null;
  response_answer: string;
  helpers: string[];
  product_id?: number | null;
  date_time?: string | null;
}

export interface SubmitStageRequest {
  checklist_request_id: number | null;
  format_id: number;
  checklist_stage_id: number | null;
  format_stage_mapping_id: number;
  action: 'submit' | 'save_draft';
  remark_id: number | null;
  remark_text: string;
  answers: SubmitStageAnswerInput[];
}

export const qcChecklistApi = {
  /** The full format -> stages -> sections -> questions tree for a format,
   * used as the rows for the checklist form. */
  getPreview: async (formatId: number): Promise<ChecklistPreview> => {
    const { data } = await apiClient.get<ChecklistPreview>('/qc-checklist/preview', {
      params: { format_id: formatId },
    });
    return data;
  },

  /** Submit or save-as-draft one stage's answers. */
  submitStage: async (request: SubmitStageRequest): Promise<void> => {
    await apiClient.post('/qc-checklist/submit-stage', request);
  },
};
