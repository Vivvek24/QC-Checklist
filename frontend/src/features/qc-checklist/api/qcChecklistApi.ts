/**
 * QC Checklist API — read the checklist structure for a format, read an
 * existing request's stages + saved answers (to resume filling), and submit a
 * stage's answers (submit / save-as-draft). Backed by the qc_checklist +
 * masters/checklist-preview endpoints.
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

/** A secondary stage (e.g. Basic Details) sent along with the primary submit.
 * The backend persists its answers and advances it to Pending. */
export interface SubmitStageExtra {
  format_stage_mapping_id: number;
  checklist_stage_id: number | null;
  answers: SubmitStageAnswerInput[];
}

export interface SubmitStageRequest {
  checklist_request_id: number | null;
  format_id: number;
  checklist_stage_id: number | null;
  format_stage_mapping_id: number;
  action: 'submit' | 'save_draft' | 'approve' | 'refer_back';
  remark_id: number | null;
  remark_text: string;
  answers: SubmitStageAnswerInput[];
  /** Secondary stages persisted + advanced to Pending with this submit. */
  extra_stages?: SubmitStageExtra[];
}

export interface SubmitStageResponse {
  success: boolean;
  checklist_request_id: number;
  checklist_stage_id: number;
  new_status: string;
  message: string;
}

/** The bare checklist_requests row (GET /qc-checklist/{id}). */
export interface ChecklistRequestResponse {
  id: number;
  request_number: string;
  format_id: number;
  status: string;
  status_format: string;
  is_last_stage: boolean;
  is_removed: boolean;
}

/** A persisted checklist_stage row (GET /qc-checklist/stages?checklist_request_id=). */
export interface ChecklistStageResponse {
  id: number;
  checklist_request_id: number;
  user_id: number | null;
  format_stage_mapping_id: number | null;
  status: string;
  is_last_stage: boolean;
}

/** A persisted question_answers row (GET /qc-checklist/question-answers?checklist_stage_id=). */
export interface SavedAnswerResponse {
  id: number;
  checklist_stage_id: number;
  question_id: number | null;
  question_option_id: number | null;
  response_question_option_id: number | null;
  stage_question_mapping_id: number | null;
  textbox_value: string;
  response_answer: string;
  product_id: number | null;
  date_time: string | null;
}

/** A persisted stage_approval_label_mappings row — who acted on each approval
 * label of a stage, with their remark and date. */
export interface ApprovalLabelMappingResponse {
  id: number;
  checklist_stage_id: number;
  approval_label_id: number;
  remark_id: number | null;
  user_id: number | null;
  role_id: number | null;
  date_of_action: string | null;
  remark: string;
  is_show: boolean;
  is_refer_back: boolean;
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

  /** Submit or save-as-draft one stage's answers. Returns the resulting
   * request/stage ids so the caller can continue the same request. */
  submitStage: async (request: SubmitStageRequest): Promise<SubmitStageResponse> => {
    const { data } = await apiClient.post<SubmitStageResponse>('/qc-checklist/submit-stage', request);
    return data;
  },

  /** Resolve a checklist request's id + format from its request_number. */
  getRequestByNumber: async (requestNumber: string): Promise<ChecklistRequestResponse | null> => {
    const { data } = await apiClient.get<{ items: ChecklistRequestResponse[] }>(
      '/qc-checklist/requests',
      { params: { search: requestNumber, limit: 50 } }
    );
    return data.items.find((r) => r.request_number === requestNumber) ?? null;
  },

  /** All stages of an existing request, with their current statuses. */
  listStagesForRequest: async (requestId: number): Promise<ChecklistStageResponse[]> => {
    const { data } = await apiClient.get<{ items: ChecklistStageResponse[] }>(
      '/qc-checklist/stages',
      { params: { checklist_request_id: requestId } }
    );
    return data.items;
  },

  /** All saved answers for one stage (to pre-fill when resuming). */
  listAnswersForStage: async (stageId: number): Promise<SavedAnswerResponse[]> => {
    const { data } = await apiClient.get<{ items: SavedAnswerResponse[] }>(
      '/qc-checklist/question-answers',
      { params: { checklist_stage_id: stageId } }
    );
    return data.items;
  },

  /** All approval-label mappings for one stage — which labels have been acted
   * on (remark + date) and which are still pending. */
  listApprovalMappingsForStage: async (stageId: number): Promise<ApprovalLabelMappingResponse[]> => {
    const { data } = await apiClient.get<{ items: ApprovalLabelMappingResponse[] }>(
      '/qc-checklist/stage-approval-label-mappings',
      { params: { checklist_stage_id: stageId } }
    );
    return data.items;
  },
};
