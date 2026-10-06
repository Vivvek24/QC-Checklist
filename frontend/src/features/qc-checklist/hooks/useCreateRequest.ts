/**
 * useCreateRequest — data loading and submission for CreateRequestPage.
 *
 * Two modes:
 *  - New request (default): user picks a format, fills the first stage, and
 *    submit/save-draft creates a brand-new request (checklist ids null — the
 *    backend creates the request + all its stages on first submit).
 *  - Continuation: opened for an existing request (from the dashboard's
 *    "Fill Next Stage" action). The hook resolves the request, loads the
 *    preview for its format and its persisted stages, then submits against
 *    the real checklist_request_id / checklist_stage_id so the request
 *    actually advances instead of a new one being created.
 *
 * The preview response already carries each stage's Template Studio column
 * layout, so there's no separate per-stage columns fetch.
 *
 * CreateRequestPage stays composition + JSX only; this hook is the page's
 * "controller".
 */

import { useRef, useState } from 'react';
import { qcChecklistApi, type SubmitStageAnswerInput, type SubmitStageExtra, type ApprovalLabelMappingResponse } from '../api/qcChecklistApi';
import type { ApprovalSnipHandle } from '../components/ApprovalSnip';
import type { ChecklistPreview, ColumnPreview } from '../models/ChecklistPreview';
import type { SavedAnswer } from '../hooks/useTemplateAnswers';
import { BASIC_DETAILS_STAGE } from '../../masters/constants';

/** Pull the human-readable message out of an API error. The backend's
 * exception-handler middleware returns `{ message }`; some endpoints use
 * FastAPI's default `{ detail }`. Try both. */
const apiErrorMessage = (e: unknown): string | undefined => {
  const data = (e as { response?: { data?: { message?: string; detail?: string } } })?.response?.data;
  return data?.message ?? data?.detail;
};

export interface SnipHandle {
  validate: () => boolean;
  getAnswers: () => SubmitStageAnswerInput[];
}

export interface UseCreateRequestResult {
  loading: boolean;
  preview: ChecklistPreview | null;
  /** Set once a format is loaded (new or continuation); drives the dropdown. */
  formatId: number | null;
  /** True while in continuation mode (resuming an existing request). */
  isContinuation: boolean;
  expandedStages: Record<number, boolean>;
  stageColumns: Record<number, ColumnPreview[]>;
  /** Pre-loaded saved answers keyed by format_stage_mapping_id → (stage_question_mapping_id → SavedAnswer). */
  savedAnswersByFsm: Record<number, Record<number, SavedAnswer>>;
  /** Persisted approval-label mappings keyed by format_stage_mapping_id. */
  approvalMappingsByFsm: Record<number, ApprovalLabelMappingResponse[]>;
  /** True while an action (submit/approve/draft/refer-back) is in flight. */
  submitting: boolean;
  snipRefs: React.RefObject<Record<number, SnipHandle | null>>;
  approvalRefs: React.RefObject<Record<number, ApprovalSnipHandle | null>>;
  handleFormatChange: (formatId: number | null) => Promise<void>;
  loadRequest: (requestNumber: string) => Promise<void>;
  toggleStage: (fsmId: number) => void;
  handleSubmit: (fsmId: number) => Promise<void>;
  handleSaveAsDraft: (fsmId: number) => Promise<void>;
  handleApprove: (fsmId: number) => Promise<void>;
  handleReferBack: (fsmId: number) => Promise<void>;
}


export interface UseCreateRequestOptions {
  onError: (detail: string) => void;
  onSubmitSuccess: () => void;
  onDraftSuccess: () => void;
  onApproveSuccess: (fullyApproved: boolean) => void;
  onReferBackSuccess: () => void;
}

export const useCreateRequest = ({
  onError,
  onSubmitSuccess,
  onDraftSuccess,
  onApproveSuccess,
  onReferBackSuccess,
}: UseCreateRequestOptions): UseCreateRequestResult => {
  const [loading, setLoading] = useState(false);
  const [preview, setPreview] = useState<ChecklistPreview | null>(null);
  const [formatId, setFormatId] = useState<number | null>(null);
  const [expandedStages, setExpandedStages] = useState<Record<number, boolean>>({});
  const [stageColumns, setStageColumns] = useState<Record<number, ColumnPreview[]>>({});
  const [savedAnswersByFsm, setSavedAnswersByFsm] = useState<Record<number, Record<number, SavedAnswer>>>({});
  const [approvalMappingsByFsm, setApprovalMappingsByFsm] = useState<Record<number, ApprovalLabelMappingResponse[]>>({});
  const [submitting, setSubmitting] = useState(false);
  const snipRefs = useRef<Record<number, SnipHandle | null>>({});
  const approvalRefs = useRef<Record<number, ApprovalSnipHandle | null>>({});

  // Continuation state: the existing request id, and a map from
  // format_stage_mapping_id -> persisted checklist_stage_id. Empty for a
  // brand-new request.
  const continuationRequestId = useRef<number | null>(null);
  const stageIdByFsm = useRef<Record<number, number>>({});
  const [isContinuation, setIsContinuation] = useState(false);

  const resetContinuation = () => {
    continuationRequestId.current = null;
    stageIdByFsm.current = {};
    setIsContinuation(false);
  };

  const applyPreview = (data: ChecklistPreview) => {
    setPreview(data);
    setFormatId(data.format_id);
    // Each stage's Template Studio column layout is already on the preview
    // response (stage.columns) — no separate per-stage fetch needed.
    setStageColumns(
      Object.fromEntries(data.stages.map((s) => [s.format_stage_mapping_id, s.columns]))
    );
  };

  const handleFormatChange = async (nextFormatId: number | null) => {
    resetContinuation();
    setSavedAnswersByFsm({});
    setApprovalMappingsByFsm({});
    if (!nextFormatId) {
      setPreview(null);
      setFormatId(null);
      setExpandedStages({});
      setStageColumns({});
      return;
    }
    setLoading(true);
    setPreview(null);
    setExpandedStages({});
    setStageColumns({});
    try {
      applyPreview(await qcChecklistApi.getPreview(nextFormatId));
    } catch (e) {
      onError(apiErrorMessage(e) || 'Failed to load checklist');
    } finally {
      setLoading(false);
    }
  };

  /** Open an existing request to continue filling its next pending stage. */
  const loadRequest = async (requestNumber: string) => {
    setLoading(true);
    setPreview(null);
    setExpandedStages({});
    setStageColumns({});
    setSavedAnswersByFsm({});
    setApprovalMappingsByFsm({});
    try {
      const request = await qcChecklistApi.getRequestByNumber(requestNumber);
      if (!request) {
        onError(`Request ${requestNumber} not found.`);
        return;
      }

      const [data, stages] = await Promise.all([
        qcChecklistApi.getPreview(request.format_id),
        qcChecklistApi.listStagesForRequest(request.id),
      ]);

      // Map persisted stages by their format_stage_mapping so submit can send
      // the real checklist_stage_id, and so the preview can reflect the live
      // per-stage status (which stage is fillable now).
      const stageIdMap: Record<number, number> = {};
      const statusByFsm: Record<number, string> = {};
      for (const s of stages) {
        if (s.format_stage_mapping_id != null) {
          stageIdMap[s.format_stage_mapping_id] = s.id;
          statusByFsm[s.format_stage_mapping_id] = s.status;
        }
      }
      continuationRequestId.current = request.id;
      stageIdByFsm.current = stageIdMap;
      setIsContinuation(true);

      // Load persisted answers for stages that already have data (any
      // non-empty status that isn't a brand-new unopened stage).
      const answersMap: Record<number, Record<number, SavedAnswer>> = {};
      const mappingsMap: Record<number, ApprovalLabelMappingResponse[]> = {};
      const fetchPromises: Promise<void>[] = [];

      for (const [fsmStr, stageId] of Object.entries(stageIdMap)) {
        const fsm = Number(fsmStr);
        const status = statusByFsm[fsm];
        if (!status || status === '') continue;

        // Load approval-label mappings for ALL touched stages (so the
        // approval snip can show who already acted on each label).
        fetchPromises.push(
          qcChecklistApi.listApprovalMappingsForStage(stageId).then((rows) => {
            mappingsMap[fsm] = rows;
          })
        );

        // Load saved answers for any stage that already has data. 'Initial'
        // is a freshly-opened stage with nothing filled yet; every other
        // status (Draft/ReferBack = editable with prior answers; Pending/
        // Approved = read-only view) has persisted answers to pre-populate.
        if (status !== 'Initial') {
          fetchPromises.push(
            qcChecklistApi.listAnswersForStage(stageId).then((rows) => {
              const byQuestion: Record<number, SavedAnswer> = {};
              for (const r of rows) {
                if (r.stage_question_mapping_id != null) {
                  byQuestion[r.stage_question_mapping_id] = {
                    textbox_value: r.textbox_value || '',
                    question_option_id: r.question_option_id,
                    response_answer: r.response_answer || '',
                  };
                }
              }
              answersMap[fsm] = byQuestion;
            })
          );
        }
      }
      await Promise.all(fetchPromises);
      setSavedAnswersByFsm(answersMap);
      setApprovalMappingsByFsm(mappingsMap);

      // Overlay the live stage statuses from the persisted request onto the
      // format preview, so the page renders the actual fillable stage(s)
      // rather than the default new-request statuses.
      applyPreview({
        ...data,
        stages: data.stages.map((st) => ({
          ...st,
          status: statusByFsm[st.format_stage_mapping_id] ?? st.status,
        })),
      });
    } catch (e) {
      onError(apiErrorMessage(e) || 'Failed to load request');
    } finally {
      setLoading(false);
    }
  };

  const toggleStage = (fsmId: number) => {
    setExpandedStages((prev) => ({ ...prev, [fsmId]: !prev[fsmId] }));
  };

  /** Normalize a Snip grid's answers to the submit API shape. */
  const toApiAnswers = (answers: SubmitStageAnswerInput[]) =>
    answers.map((a) => ({
      stage_question_mapping_id: a.stage_question_mapping_id,
      question_id: a.question_id,
      textbox_value: a.textbox_value,
      question_option_id: a.question_option_id,
      response_answer: a.response_answer,
      product_id: a.product_id ?? null,
      date_time: a.date_time ?? null,
      helpers: a.helpers.length > 0 ? a.helpers : [],
    }));

  /** Basic Details is the request header: it has no Submit button of its own,
   * so on the first submit of a new request its answers are sent as an extra
   * stage. The backend persists them and advances Basic Details to Pending so
   * the request becomes visible on the dashboard. */
  const buildBasicDetailsExtra = (submittedFsmId: number): SubmitStageExtra[] => {
    if (!preview) return [];
    const basic = preview.stages.find((s) => s.stage_name === BASIC_DETAILS_STAGE);
    // Nothing to do if there's no Basic Details, it's the stage being
    // submitted, or it's already past its fillable state.
    if (!basic || basic.format_stage_mapping_id === submittedFsmId) return [];
    if (!['Initial', 'Draft', 'ReferBack'].includes(basic.status)) return [];

    const basicAnswers = snipRefs.current[basic.format_stage_mapping_id]?.getAnswers() ?? [];
    return [{
      format_stage_mapping_id: basic.format_stage_mapping_id,
      checklist_stage_id: stageIdByFsm.current[basic.format_stage_mapping_id] ?? null,
      answers: toApiAnswers(basicAnswers),
    }];
  };

  /** Submit or save-as-draft one specific stage's answers (the stage whose
   * action button was clicked), validating only that stage. */
  const submitStageByFsm = async (fsmId: number, action: 'submit' | 'save_draft' | 'approve' | 'refer_back') => {
    if (!preview) return null;
    const stage = preview.stages.find((s) => s.format_stage_mapping_id === fsmId);
    if (!stage) return null;

    const ref = snipRefs.current[fsmId];
    const answers = ref?.getAnswers() ?? [];

    // Remark comes from this stage's approval section (absent on Basic
    // Details, which has no approval snip — then there's no remark to send).
    const remark = approvalRefs.current[fsmId]?.getRemark();

    return qcChecklistApi.submitStage({
      checklist_request_id: continuationRequestId.current,
      format_id: preview.format_id,
      checklist_stage_id: stageIdByFsm.current[fsmId] ?? null,
      format_stage_mapping_id: fsmId,
      action,
      remark_id: remark?.remark_id ?? null,
      remark_text: remark?.remark_text ?? '',
      answers: toApiAnswers(answers),
      // On submit, carry Basic Details along so the header stage is persisted
      // and moved to Pending (not applicable to save-as-draft).
      extra_stages: action === 'submit' ? buildBasicDetailsExtra(fsmId) : undefined,
    });
  };

  const handleSubmit = async (fsmId: number) => {
    // Validate the stage being submitted: its grid, then its remark.
    let allValid = true;
    const snipRef = snipRefs.current[fsmId];
    if (snipRef && !snipRef.validate()) allValid = false;

    const approvalRef = approvalRefs.current[fsmId];
    if (approvalRef && !approvalRef.validateRemark()) allValid = false;

    // On first submit, Basic Details rides along — validate its grid too.
    if (preview) {
      const basic = preview.stages.find((s) => s.stage_name === BASIC_DETAILS_STAGE);
      if (basic && basic.format_stage_mapping_id !== fsmId && ['Initial', 'Draft', 'ReferBack'].includes(basic.status)) {
        const basicSnip = snipRefs.current[basic.format_stage_mapping_id];
        if (basicSnip && !basicSnip.validate()) allValid = false;
      }
    }

    if (!allValid) {
      onError('Please fill all required fields.');
      return;
    }
    setSubmitting(true);
    try {
      await submitStageByFsm(fsmId, 'submit');
      onSubmitSuccess();
    } catch (e) {
      setSubmitting(false);
      onError(apiErrorMessage(e) || 'Submit failed');
    }
  };

  const handleSaveAsDraft = async (fsmId: number) => {
    setSubmitting(true);
    try {
      await submitStageByFsm(fsmId, 'save_draft');
      onDraftSuccess();
    } catch (e) {
      setSubmitting(false);
      onError(apiErrorMessage(e) || 'Save failed');
    }
  };

  const handleApprove = async (fsmId: number) => {
    // Validate the grid (single-label stages fill + approve in one step, so
    // the data must be valid) and the remark (the actor must pick one).
    let allValid = true;
    const snipRef = snipRefs.current[fsmId];
    if (snipRef && !snipRef.validate()) allValid = false;

    const approvalRef = approvalRefs.current[fsmId];
    if (approvalRef && !approvalRef.validateRemark()) allValid = false;

    if (!allValid) {
      onError('Please fill all required fields and select a remark.');
      return;
    }
    setSubmitting(true);
    try {
      const result = await submitStageByFsm(fsmId, 'approve');
      const fullyApproved = result?.message?.includes('fully approved') ?? false;
      onApproveSuccess(fullyApproved);
    } catch (e) {
      setSubmitting(false);
      onError(apiErrorMessage(e) || 'Approve failed');
    }
  };

  const handleReferBack = async (fsmId: number) => {
    const approvalRef = approvalRefs.current[fsmId];
    if (approvalRef && !approvalRef.validateRemark()) {
      onError('Please select a remark before referring back.');
      return;
    }
    setSubmitting(true);
    try {
      await submitStageByFsm(fsmId, 'refer_back');
      onReferBackSuccess();
    } catch (e) {
      setSubmitting(false);
      onError(apiErrorMessage(e) || 'Refer back failed');
    }
  };

  return {
    loading,
    preview,
    formatId,
    isContinuation,
    expandedStages,
    stageColumns,
    savedAnswersByFsm,
    approvalMappingsByFsm,
    submitting,
    snipRefs,
    approvalRefs,
    handleFormatChange,
    loadRequest,
    toggleStage,
    handleSubmit,
    handleSaveAsDraft,
    handleApprove,
    handleReferBack,
  };
};
