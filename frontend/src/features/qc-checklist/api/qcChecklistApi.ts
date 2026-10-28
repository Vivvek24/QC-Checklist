/**
 * QC Checklist API — read the checklist structure for a format, read an
 * existing request's stages + saved answers (to resume filling), and submit a
 * stage's answers (submit / save-as-draft). Backed by the qc_checklist +
 * masters/checklist-preview endpoints.
 */

import { apiClient } from '@shared/services/apiClient';
import type { ChecklistPreview } from '../models/ChecklistPreview';

/** A sub-question's answer, sent nested under its parent answer. Persisted as
 * its own question_answers row linked via the self-join. */
export interface SubAnswerInput {
  question_id: number;
  textbox_value: string;
  question_option_id: number | null;
  response_question_option_id?: number | null;
  response_answer: string;
}

/** One row's answer, as returned by any Snip grid's getAnswers(). Optional
 * fields cover shapes only ReconcilationSheetSnip currently produces. */
export interface SubmitStageAnswerInput {
  stage_question_mapping_id: number;
  question_id: number;
  textbox_value: string;
  question_option_id: number | null;
  response_question_option_id?: number | null;
  response_answer: string;
  helpers: string[];
  product_id?: number | null;
  date_time?: string | null;
  /** Calculated-question accumulation (parent textbox cleared; values in helpers). */
  has_helper?: boolean;
  answer_total_vails?: number;
  /** Answers for this question's sub-questions (if any). */
  sub_answers?: SubAnswerInput[];
}

/** A secondary stage (e.g. Basic Details) sent along with the primary submit.
 * The backend persists its answers and advances it to Pending. */
export interface SubmitStageExtra {
  format_stage_mapping_id: number;
  checklist_stage_id: number | null;
  answers: SubmitStageAnswerInput[];
  /** Per-question approval remark picks for this extra stage's questions. */
  question_approvals?: QuestionApprovalInput[];
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
  /** Per-question approval remark picks for the primary stage's questions. */
  question_approvals?: QuestionApprovalInput[];
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

/** A saved sub-question answer (GET /qc-checklist/question-answers/sub-answers). */
export interface SubAnswerResponse {
  question_id: number;
  question_option_id: number | null;
  response_question_option_id: number | null;
  textbox_value: string;
  response_answer: string;
}

/** A parent question's saved sub-answers, grouped by the parent's question_id. */
export interface ParentSubAnswersResponse {
  parent_question_id: number;
  sub_answers: SubAnswerResponse[];
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
  /** Accumulated total for a calculated question (answer_total_vails). */
  answer_total_vails: number;
  /** Calculated-question "+ Add" helper values. */
  helpers: string[];
  /** Auto-generated per-test row fields (set when a product expands into
   * per-test rows; these rows have stage_question_mapping_id = null). */
  test_title: string;
  sample_vails: string;
  has_vails: boolean;
  serial_number: number;
  /** Issue Vials state — who issued, who received, and when. */
  receiver_user_id: number | null;
  receiver_name: string;
  issuer_name: string;
  issued_by_date: string | null;
  received_by_date: string | null;
  is_issued_vails: boolean;
}

/** A persisted stage_approval_label_mappings row — who acted on each approval
 * label of a stage, with their remark and date. */
export interface ApprovalLabelMappingResponse {
  id: number;
  checklist_stage_id: number | null;
  /** Set for per-question approval rows (null for stage-level rows). */
  question_answer_id: number | null;
  approval_label_id: number;
  remark_id: number | null;
  user_id: number | null;
  role_id: number | null;
  date_of_action: string | null;
  remark: string;
  is_show: boolean;
  is_refer_back: boolean;
}

/** One per-question approval remark pick, sent in the submit payload. */
export interface QuestionApprovalInput {
  stage_question_mapping_id: number;
  approval_label_id: number;
  remark_id: number | null;
  remark_text: string;
}

/** A persisted stage's identity + live status, from the request-detail
 * aggregate (keyed by format_stage_mapping_id so it overlays the preview). */
export interface StageStateResponse {
  format_stage_mapping_id: number | null;
  checklist_stage_id: number;
  status: string;
}

/** All saved data for one stage, grouped under its format stage mapping — the
 * per-stage block of the request-detail aggregate. */
export interface StageAnswersBlockResponse {
  format_stage_mapping_id: number | null;
  checklist_stage_id: number;
  answers: SavedAnswerResponse[];
  sub_answers: ParentSubAnswersResponse[];
  approval_mappings: ApprovalLabelMappingResponse[];
}

/** The full fill-page payload for one request, returned by the single
 * request-detail endpoint — preview tree + per-stage statuses + all saved
 * answers / sub-answers / approval mappings in one response. */
export interface ChecklistRequestDetailResponse {
  request_id: number;
  request_number: string;
  format_id: number;
  preview: ChecklistPreview;
  stages: StageStateResponse[];
  answer_blocks: StageAnswersBlockResponse[];
  question_approvals: ApprovalLabelMappingResponse[];
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

  /** The full fill-page payload for an existing request in ONE call: the format
   * preview tree, each stage's live status, and every stage's saved answers /
   * sub-answers / approval mappings. Replaces the previous per-stage fan-out
   * (preview + stages + 3 calls per stage). Backed by
   * GET /qc-checklist/requests/{request_number}/detail. */
  getRequestDetail: async (requestNumber: string): Promise<ChecklistRequestDetailResponse> => {
    const { data } = await apiClient.get<ChecklistRequestDetailResponse>(
      `/qc-checklist/requests/${encodeURIComponent(requestNumber)}/detail`
    );
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

  /** Saved sub-question answers for one stage, grouped by parent question_id
   * (to pre-fill each sub-question's input when resuming / viewing). */
  listSubAnswersForStage: async (stageId: number): Promise<ParentSubAnswersResponse[]> => {
    const { data } = await apiClient.get<{ items: ParentSubAnswersResponse[] }>(
      '/qc-checklist/question-answers/sub-answers',
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

  /** All per-question approval-label mappings for a whole request (keyed by
   * question_answer_id), to pre-fill each question's approval remark. */
  listQuestionApprovalMappingsForRequest: async (requestId: number): Promise<ApprovalLabelMappingResponse[]> => {
    const { data } = await apiClient.get<{ items: ApprovalLabelMappingResponse[] }>(
      '/qc-checklist/stage-approval-label-mappings',
      { params: { checklist_request_id: requestId } }
    );
    return data.items;
  },

  /** Download the request rendered as a PDF (format-agnostic). Triggers a
   * browser "Save As" using the server-provided filename. */
  downloadRequestPdf: async (requestNumber: string): Promise<void> => {
    const { data } = await apiClient.get<Blob>(
      `/qc-checklist/${encodeURIComponent(requestNumber)}/pdf`,
      { responseType: 'blob' }
    );
    const url = window.URL.createObjectURL(data);
    const link = document.createElement('a');
    link.href = url;
    link.download = `${requestNumber}.pdf`;
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);
  },

  /** The tests configured for a product (test master). Used to preview the
   * per-test rows a product expands into when it's picked on Basic Details —
   * mirrors the backend _expand_product_tests mapping (nothing is persisted
   * until the stage is submitted). */
  listTestsForProduct: async (productId: number): Promise<ProductTestResponse[]> => {
    const { data } = await apiClient.get<{ items: ProductTestResponse[] }>(
      '/masters/test-masters',
      { params: { product_id: productId } }
    );
    return data.items;
  },

  /** Active users with a given role code (e.g. ANALYST) — for the Issue Vials
   * "Issued By" user dropdown. */
  listUsersByRole: async (roleCode: string): Promise<RoleUserResponse[]> => {
    const { data } = await apiClient.get<{ users: RoleUserResponse[] }>(
      '/users/by-role',
      { params: { role_code: roleCode } }
    );
    return data.users;
  },

  /** Persist the "Issue Vials" action on a test-row answer: records the
   * receiving analyst and stamps the issue/received dates + issuer server-side.
   * Returns the updated answer so the grid can reflect it immediately.
   * Backed by POST /qc-checklist/question-answers/{answerId}/issue-vials. */
  issueVials: async (answerId: number, receiverUserId: number): Promise<SavedAnswerResponse> => {
    const { data } = await apiClient.post<SavedAnswerResponse>(
      `/qc-checklist/question-answers/${answerId}/issue-vials`,
      { receiver_user_id: receiverUserId }
    );
    return data;
  },

  /** Compute the "Remaining Samples destroyed By" value for a recon Test stage
   * answer (received_total - sample_consumed), server-side. Returns the updated
   * answer (textbox_value = destroyed). Throws 400 with the Mendix validation
   * message when vials are unissued / product not picked / result negative.
   * Backed by POST /qc-checklist/question-answers/{answerId}/calculate-sample-destroyed. */
  calculateSampleDestroyed: async (answerId: number): Promise<SavedAnswerResponse> => {
    const { data } = await apiClient.post<SavedAnswerResponse>(
      `/qc-checklist/question-answers/${answerId}/calculate-sample-destroyed`,
      {}
    );
    return data;
  },
};

/** A user as returned by GET /users/by-role. */
export interface RoleUserResponse {
  id: number;
  username: string;
  employee_name: string | null;
}

/** A test master row as returned by GET /masters/test-masters?product_id=. */
export interface ProductTestResponse {
  id: number;
  test_name: string;
  sample_description: string;
  sample_qty: number;
}
