/**
 * useChecklistWorkflow — checklist data loading + the stage lifecycle actions
 * (submit / save-as-draft / approve / refer-back) for a request.
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
import { qcChecklistApi, type SubmitStageAnswerInput, type SubmitStageExtra, type ApprovalLabelMappingResponse, type QuestionApprovalInput } from '../api/qcChecklistApi';
import type { ApprovalSnipHandle } from '../components/ApprovalSnip';
import type { ChecklistPreview, ColumnPreview } from '../models/ChecklistPreview';
import type { SavedAnswer, SavedSubAnswer } from './useValidateTemplateAnswers';
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
  /** Per-question approval remark picks (grids without approvable questions omit this). */
  getQuestionApprovals?: () => QuestionApprovalInput[];
}

/** An auto-generated per-test row (persisted question_answer with no
 * stage_question_mapping / question — its test_title acts as the row title).
 * Rendered as read-only grid rows by TemplateDrivenSnip. */
export interface TestRow {
  id: number;
  test_title: string;
  sample_vails: string;
  has_vails: boolean;
  serial_number: number;
  /** Issue Vials state for the row. */
  receiver_user_id: number | null;
  receiver_name: string;
  issuer_name: string;
  issued_by_date: string | null;
  received_by_date: string | null;
  is_issued_vails: boolean;
}

export interface UseChecklistWorkflowResult {
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
  /** Pre-loaded saved sub-answers keyed by format_stage_mapping_id → (parent question_id → SavedSubAnswer[]). */
  savedSubAnswersByFsm: Record<number, Record<number, SavedSubAnswer[]>>;
  /** Persisted approval-label mappings keyed by format_stage_mapping_id. */
  approvalMappingsByFsm: Record<number, ApprovalLabelMappingResponse[]>;
  /** Per-question approval mappings for the whole request (keyed by question_answer_id). */
  questionApprovalMappings: ApprovalLabelMappingResponse[];
  /** question_answer_id -> stage_question_mapping_id, from the loaded answers. */
  sqmByQuestionAnswerId: Record<number, number>;
  /** Auto-generated per-test rows keyed by format_stage_mapping_id (rows whose
   * stage_question_mapping_id is null — their test_title is the row title). */
  testRowsByFsm: Record<number, TestRow[]>;
  /** Preview the per-test rows a product expands into, on the stage after
   * Basic Details — called from the Masters product dropdown's onChange. These
   * are shown immediately but only persisted when the stage is submitted.
   * Passing null clears the previewed rows. */
  previewTestRowsForProduct: (productId: number | null) => Promise<void>;
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


export interface UseChecklistWorkflowOptions {
  onError: (detail: string) => void;
  onSubmitSuccess: () => void;
  onDraftSuccess: () => void;
  onApproveSuccess: (fullyApproved: boolean) => void;
  onReferBackSuccess: () => void;
}

export const useChecklistWorkflow = ({
  onError,
  onSubmitSuccess,
  onDraftSuccess,
  onApproveSuccess,
  onReferBackSuccess,
}: UseChecklistWorkflowOptions): UseChecklistWorkflowResult => {
  const [loading, setLoading] = useState(false);
  const [preview, setPreview] = useState<ChecklistPreview | null>(null);
  const [formatId, setFormatId] = useState<number | null>(null);
  const [expandedStages, setExpandedStages] = useState<Record<number, boolean>>({});
  const [stageColumns, setStageColumns] = useState<Record<number, ColumnPreview[]>>({});
  const [savedAnswersByFsm, setSavedAnswersByFsm] = useState<Record<number, Record<number, SavedAnswer>>>({});
  const [savedSubAnswersByFsm, setSavedSubAnswersByFsm] = useState<Record<number, Record<number, SavedSubAnswer[]>>>({});
  const [approvalMappingsByFsm, setApprovalMappingsByFsm] = useState<Record<number, ApprovalLabelMappingResponse[]>>({});
  // Per-question approval mappings for the whole request + a question_answer_id
  // -> stage_question_mapping_id map, so the grid can pre-fill acted remarks.
  const [questionApprovalMappings, setQuestionApprovalMappings] = useState<ApprovalLabelMappingResponse[]>([]);
  const [sqmByQuestionAnswerId, setSqmByQuestionAnswerId] = useState<Record<number, number>>({});
  const [testRowsByFsm, setTestRowsByFsm] = useState<Record<number, TestRow[]>>({});
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
    setSavedSubAnswersByFsm({});
    setApprovalMappingsByFsm({});
    setQuestionApprovalMappings([]);
    setSqmByQuestionAnswerId({});
    setTestRowsByFsm({});
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
    setSavedSubAnswersByFsm({});
    setApprovalMappingsByFsm({});
    setQuestionApprovalMappings([]);
    setSqmByQuestionAnswerId({});
    setTestRowsByFsm({});
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
      const subAnswersMap: Record<number, Record<number, SavedSubAnswer[]>> = {};
      const mappingsMap: Record<number, ApprovalLabelMappingResponse[]> = {};
      const qaToSqm: Record<number, number> = {};
      const testMap: Record<number, TestRow[]> = {};
      const fetchPromises: Promise<void>[] = [];

      // Per-question approval mappings for the whole request (keyed by
      // question_answer_id) — pre-fills each question's acted approval remark.
      let questionApprovals: ApprovalLabelMappingResponse[] = [];
      fetchPromises.push(
        qcChecklistApi.listQuestionApprovalMappingsForRequest(request.id).then((rows) => {
          questionApprovals = rows;
        })
      );

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
        // is normally a freshly-opened stage with nothing filled yet — EXCEPT
        // for a ReconcilationSheet, whose Test stage carries the auto-generated
        // per-test (Issue Vials) rows while it stays Initial through the
        // supervisor's issuing phase. So for recon, also load Initial stages so
        // those test rows show on the fill-next-stage page.
        const isRecon = data.format_type === 'ReconcilationSheet';
        if (status !== 'Initial' || isRecon) {
          fetchPromises.push(
            qcChecklistApi.listAnswersForStage(stageId).then((rows) => {
              const byQuestion: Record<number, SavedAnswer> = {};
              const testRows: TestRow[] = [];
              for (const r of rows) {
                if (r.stage_question_mapping_id != null) {
                  byQuestion[r.stage_question_mapping_id] = {
                    textbox_value: r.textbox_value || '',
                    question_option_id: r.question_option_id,
                    response_question_option_id: r.response_question_option_id,
                    product_id: r.product_id,
                    date_time: r.date_time ?? null,
                    response_answer: r.response_answer || '',
                    answer_total_vails: r.answer_total_vails ?? 0,
                    helpers: r.helpers ?? [],
                  };
                  // question_answer_id -> sqm, so per-question approval mappings
                  // (keyed by question_answer_id) can attach to the right row.
                  qaToSqm[r.id] = r.stage_question_mapping_id;
                } else if (r.test_title) {
                  // Auto-generated per-test row (no stage_question_mapping):
                  // its test_title acts as the row title, sample_vails its
                  // sample description. Rendered as read-only grid rows.
                  testRows.push({
                    id: r.id,
                    test_title: r.test_title,
                    sample_vails: r.sample_vails || '',
                    has_vails: r.has_vails,
                    serial_number: r.serial_number,
                    receiver_user_id: r.receiver_user_id ?? null,
                    receiver_name: r.receiver_name || '',
                    issuer_name: r.issuer_name || '',
                    issued_by_date: r.issued_by_date ?? null,
                    received_by_date: r.received_by_date ?? null,
                    is_issued_vails: r.is_issued_vails ?? false,
                  });
                }
              }
              answersMap[fsm] = byQuestion;
              if (testRows.length > 0) {
                testRows.sort((a, b) => a.serial_number - b.serial_number);
                testMap[fsm] = testRows;
              }
            })
          );
          // Saved sub-question answers, grouped by parent question_id.
          fetchPromises.push(
            qcChecklistApi.listSubAnswersForStage(stageId).then((groups) => {
              const byParent: Record<number, SavedSubAnswer[]> = {};
              for (const g of groups) {
                byParent[g.parent_question_id] = g.sub_answers.map((s) => ({
                  question_id: s.question_id,
                  textbox_value: s.textbox_value || '',
                  question_option_id: s.question_option_id,
                  response_answer: s.response_answer || '',
                }));
              }
              subAnswersMap[fsm] = byParent;
            })
          );
        }
      }
      await Promise.all(fetchPromises);
      setSavedAnswersByFsm(answersMap);
      setSavedSubAnswersByFsm(subAnswersMap);
      setApprovalMappingsByFsm(mappingsMap);
      setQuestionApprovalMappings(questionApprovals);
      setSqmByQuestionAnswerId(qaToSqm);
      setTestRowsByFsm(testMap);

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
      response_question_option_id: a.response_question_option_id ?? null,
      response_answer: a.response_answer,
      product_id: a.product_id ?? null,
      date_time: a.date_time ?? null,
      has_helper: a.has_helper ?? false,
      answer_total_vails: a.answer_total_vails ?? 0,
      helpers: a.helpers.length > 0 ? a.helpers : [],
      sub_answers: a.sub_answers && a.sub_answers.length > 0 ? a.sub_answers : undefined,
    }));

  /** Basic Details is the request header: it has no Submit button of its own,
   * so on the first submit of a new request its answers are sent as an extra
   * stage. The backend persists them and advances Basic Details to Pending so
   * the request becomes visible on the dashboard. */
  /** Recon analyst phase: all vials on the Test stage have been issued. In this
   * phase the analyst edits the is_calculated "Sample Quantity Received" on the
   * (Pending) Basic Details stage, so it must ride along on the submit. */
  const isReconAnalystPhase = (): boolean => {
    if (preview?.format_type !== 'ReconcilationSheet') return false;
    const testStage = preview.stages.find((s) => s.stage_name !== BASIC_DETAILS_STAGE
      && (testRowsByFsm[s.format_stage_mapping_id]?.length ?? 0) > 0);
    if (!testStage) return false;
    const rows = testRowsByFsm[testStage.format_stage_mapping_id] ?? [];
    return rows.length > 0 && !rows.some((r) => r.has_vails && !r.received_by_date);
  };

  const buildBasicDetailsExtra = (submittedFsmId: number): SubmitStageExtra[] => {
    if (!preview) return [];
    const basic = preview.stages.find((s) => s.stage_name === BASIC_DETAILS_STAGE);
    // Nothing to do if there's no Basic Details or it's the stage being submitted.
    if (!basic || basic.format_stage_mapping_id === submittedFsmId) return [];
    // Normally only ride along while Basic Details is still fillable. In the
    // recon analyst phase it's Pending but the analyst just edited the
    // is_calculated answer, so include it then too.
    const fillable = ['Initial', 'Draft', 'ReferBack'].includes(basic.status);
    if (!fillable && !isReconAnalystPhase()) return [];

    const basicRef = snipRefs.current[basic.format_stage_mapping_id];
    const basicAnswers = basicRef?.getAnswers() ?? [];
    const basicApprovals = basicRef?.getQuestionApprovals?.() ?? [];
    return [{
      format_stage_mapping_id: basic.format_stage_mapping_id,
      checklist_stage_id: stageIdByFsm.current[basic.format_stage_mapping_id] ?? null,
      answers: toApiAnswers(basicAnswers),
      question_approvals: basicApprovals.length > 0 ? basicApprovals : undefined,
    }];
  };

  /** Submit or save-as-draft one specific stage's answers (the stage whose
   * action button was clicked), validating only that stage. */
  const submitStageByFsm = async (fsmId: number, action: 'submit' | 'save_draft' | 'approve' | 'refer_back') => {
    if (!preview) return null;
    const stage = preview.stages.find((s) => s.format_stage_mapping_id === fsmId);
    if (!stage) return null;

    const ref = snipRefs.current[fsmId];
    const gridAnswers = ref?.getAnswers() ?? [];
    // Declaration answers come from the ApprovalSnip (hidden from the main grid)
    // and are persisted alongside the stage's grid answers.
    const declarationAnswers = approvalRefs.current[fsmId]?.getDeclarationAnswers?.() ?? [];
    const answers = [...gridAnswers, ...declarationAnswers];
    const questionApprovals = ref?.getQuestionApprovals?.() ?? [];

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
      // Per-question approval remark picks for this stage's approvable questions.
      question_approvals: questionApprovals.length > 0 ? questionApprovals : undefined,
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

    // Recon sheet: the remark is NOT mandatory during the supervisor's vial-
    // issuing phase. It becomes mandatory in the analyst phase (all vials
    // issued), which is where the analyst submits with their remark. Other
    // formats always require it.
    const isReconSheet = preview?.format_type === 'ReconcilationSheet';
    const analystPhase = isReconAnalystPhase();
    const skipRemark = isReconSheet && !analystPhase;

    const approvalRef = approvalRefs.current[fsmId];
    if (!skipRemark && approvalRef && !approvalRef.validateRemark()) allValid = false;
    if (approvalRef && !approvalRef.validateDeclarations()) allValid = false;

    // Basic Details rides along + is validated when it's still fillable (first
    // submit) OR in the recon analyst phase (where the analyst edited its
    // is_calculated "Sample Quantity Received" — its required check must hit).
    if (preview) {
      const basic = preview.stages.find((s) => s.stage_name === BASIC_DETAILS_STAGE);
      const basicFillable = basic && ['Initial', 'Draft', 'ReferBack'].includes(basic.status);
      if (basic && basic.format_stage_mapping_id !== fsmId && (basicFillable || analystPhase)) {
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
    if (approvalRef && !approvalRef.validateDeclarations()) allValid = false;

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

  /** The format_stage_mapping_id of the stage immediately after Basic Details
   * (preview stages are already in format-stage order). Null if there's no
   * Basic Details or no following stage. */
  const nextFsmAfterBasicDetails = (): number | null => {
    if (!preview) return null;
    const idx = preview.stages.findIndex((s) => s.stage_name === BASIC_DETAILS_STAGE);
    if (idx < 0 || idx + 1 >= preview.stages.length) return null;
    return preview.stages[idx + 1]!.format_stage_mapping_id;
  };

  /** Preview the per-test rows a product expands into on the next stage. Mirrors
   * the backend _expand_product_tests mapping (test_title = test name,
   * sample_vails = sample description, has_vails = sample_qty != 0) but only in
   * memory — persistence happens on submit. */
  const previewTestRowsForProduct = async (productId: number | null): Promise<void> => {
    const nextFsm = nextFsmAfterBasicDetails();
    if (nextFsm == null) return;
    if (productId == null) {
      setTestRowsByFsm((prev) => ({ ...prev, [nextFsm]: [] }));
      seedSampleConsumed(nextFsm, 0);
      return;
    }
    try {
      const tests = await qcChecklistApi.listTestsForProduct(productId);
      const rows: TestRow[] = tests.map((t, i) => ({
        id: -(t.id || i + 1), // negative synthetic id — not a persisted row yet
        receiver_user_id: null,
        receiver_name: '',
        issuer_name: '',
        issued_by_date: null,
        received_by_date: null,
        is_issued_vails: false,
        test_title: t.test_name,
        sample_vails: t.sample_description || '',
        has_vails: t.sample_qty !== 0,
        serial_number: i + 1,
      }));
      setTestRowsByFsm((prev) => ({ ...prev, [nextFsm]: rows }));

      // Populate the next stage's "Calculate_SampleConsumed" question with the
      // total of the SAME tests' sample_qty (consistent with the test rows).
      const total = tests.reduce((sum, t) => sum + (t.sample_qty ?? 0), 0);
      seedSampleConsumed(nextFsm, total);
    } catch (e) {
      onError(apiErrorMessage(e) || 'Failed to load product tests');
    }
  };

  /** Seed (or clear) the next stage's Calculate_SampleConsumed answer with a
   * computed total, written as a saved answer keyed by that question's
   * stage_question_mapping_id so the stage's grid / declaration grid shows it
   * (read-only). */
  const seedSampleConsumed = (fsm: number, total: number) => {
    const stage = preview?.stages.find((s) => s.format_stage_mapping_id === fsm);
    if (!stage) return;
    const allQ = [
      ...stage.questions,
      ...stage.sections.flatMap((sec) => sec.questions),
    ];
    const target = allQ.find((q) => q.custom_answers === 'Calculate_SampleConsumed');
    if (!target) return;
    const key = target.stage_question_mapping_id;
    setSavedAnswersByFsm((prev) => {
      const forFsm = { ...(prev[fsm] ?? {}) };
      forFsm[key] = {
        ...(forFsm[key] ?? {
          question_option_id: null,
          response_question_option_id: null,
          product_id: null,
          response_answer: '',
        }),
        textbox_value: String(total),
      };
      return { ...prev, [fsm]: forFsm };
    });
  };

  return {
    loading,
    preview,
    formatId,
    isContinuation,
    expandedStages,
    stageColumns,
    savedAnswersByFsm,
    savedSubAnswersByFsm,
    approvalMappingsByFsm,
    questionApprovalMappings,
    sqmByQuestionAnswerId,
    testRowsByFsm,
    previewTestRowsForProduct,
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
