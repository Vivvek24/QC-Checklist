/**
 * useTemplateDrivenSnip — the orchestration behind TemplateDrivenSnip.
 *
 * Composes the three concerns the grid needs — answer state/validation
 * (useValidateTemplateAnswers), SAP auto-fill (useSetSapAnswers), and
 * per-question approval remarks (useQuestionApprovals) — and builds the
 * access objects + imperative-handle methods the component renders from.
 *
 * TemplateDrivenSnip itself stays pure render (tables + cells); all wiring
 * lives here.
 */

import type { ColumnPreview, QuestionAnswerPreview } from '../models/ChecklistPreview';
import type { ApprovalLabelMappingResponse, QuestionApprovalInput } from '../api/qcChecklistApi';
import type { TemplateAnswer } from '../models/TemplateTypes';
import { BASIC_DETAILS_STAGE } from '../../masters/constants';
import { useRemarks } from '../../masters/hooks/useRemarks';
import { useProducts } from '../../masters/hooks/useProducts';
import { useResolvedColumns } from './useResolvedColumns';
import { useValidateTemplateAnswers, type SavedAnswer, type SavedSubAnswer, type RowErrors } from './useValidateTemplateAnswers';
import { useSetSapAnswers } from './useSetSapAnswers';
import { useQuestionApprovals } from './useQuestionApprovals';
import type { SubAnswerAccess, QuestionApprovalAccess } from '../components/TemplateCell';

const OTHERS_REMARK = 'Others';

export interface UseTemplateDrivenSnipOptions {
  questions: QuestionAnswerPreview[];
  columns: ColumnPreview[];
  stageName: string;
  stageStatus: string;
  sections: { questions: QuestionAnswerPreview[]; columns: ColumnPreview[] }[];
  hasSection: boolean;
  /** True when the request's format is ReconcilationSheet — relaxes the
   * calculated-total + helper required checks at submit. */
  isReconSheet?: boolean;
  savedAnswers?: Record<number, SavedAnswer>;
  savedSubAnswers?: Record<number, SavedSubAnswer[]>;
  questionApprovalMappings?: ApprovalLabelMappingResponse[];
  sqmByQuestionAnswerId?: Record<number, number>;
  userNameById?: (userId: number) => string;
}

export interface TemplateDrivenSnipState {
  /** All questions the stage carries (flattened across sections). */
  allQuestions: QuestionAnswerPreview[];
  /** True while the stage is editable by the filling analyst. */
  canAdd: boolean;
  isBasicDetails: boolean;

  // answer state + setters
  selections: Record<number, unknown>;
  setSelections: React.Dispatch<React.SetStateAction<Record<number, unknown>>>;
  answers: Record<number, string>;
  setAnswers: React.Dispatch<React.SetStateAction<Record<number, string>>>;
  responses: Record<number, string>;
  setResponses: React.Dispatch<React.SetStateAction<Record<number, string>>>;
  responseOptionSelections: Record<number, number | null>;
  setResponseOptionSelections: React.Dispatch<React.SetStateAction<Record<number, number | null>>>;
  productSelections: Record<number, number | null>;
  setProductSelections: React.Dispatch<React.SetStateAction<Record<number, number | null>>>;
  /** Pick a product on a Masters row — records the selection and auto-fills any
   * has_associated_master question with the product's storage conditions. */
  onProductPicked: (key: number, productId: number | null) => void;
  /** Product master options for "Masters" questions ({label, value}). */
  productOptions: { label: string; value: number }[];
  dateSelections: Record<number, Date | null>;
  setDateSelections: React.Dispatch<React.SetStateAction<Record<number, Date | null>>>;
  helpers: Record<number, string[]>;
  setHelpers: React.Dispatch<React.SetStateAction<Record<number, string[]>>>;
  /** Running total (answer_total_vails) per calculated-question row. */
  totals: Record<number, number>;
  /** "+ Add" action for a calculated question (validates + folds into a helper). */
  addCalculatedHelper: (key: number) => boolean;
  /** Remove a calculated helper at idx (subtracts its value from the total). */
  removeCalculatedHelper: (key: number, idx: number) => void;
  /** Live-validate a calculated question's typed value. */
  validateCalculatedValue: (key: number, value: string) => void;
  errors: Record<number, RowErrors>;
  helperErrors: Record<number, (string | undefined)[]>;
  clearError: (key: number, field: keyof RowErrors) => void;
  clearHelperError: (key: number, idx: number) => void;

  // SAP auto-fill
  sapTriggerKey: number | null;
  fetchFromSap: () => Promise<void> | void;
  sapLoading: boolean;
  sapError: string | null;

  // cell access objects
  subAccess: SubAnswerAccess;
  approvalAccess: QuestionApprovalAccess;

  // imperative-handle methods
  validateAll: () => boolean;
  getAnswers: () => TemplateAnswer[];
  getQuestionApprovals: () => QuestionApprovalInput[];
}

export const useTemplateDrivenSnip = ({
  questions,
  columns,
  stageName,
  stageStatus,
  sections,
  hasSection,
  isReconSheet = false,
  savedAnswers,
  savedSubAnswers,
  questionApprovalMappings,
  sqmByQuestionAnswerId,
  userNameById,
}: UseTemplateDrivenSnipOptions): TemplateDrivenSnipState => {
  const isBasicDetails = stageName === BASIC_DETAILS_STAGE;
  // Editable only while the stage is still fillable; once submitted (Pending)
  // or approved it's view-only until the approver acts.
  const canAdd = stageStatus === 'Initial' || stageStatus === 'Draft' || stageStatus === 'ReferBack';

  // Flatten every question — flat questions or all section questions — so the
  // answer hook validates/returns the whole stage. Declaration questions are
  // excluded here: they render + are answered in the ApprovalSnip, not this grid.
  const allQuestions: QuestionAnswerPreview[] = (
    hasSection ? sections.flatMap((s) => s.questions) : questions
  ).filter((q) => !q.is_declaration_question);

  // Column-type flags from the union of stage + section columns.
  const unionColumns = hasSection ? sections.flatMap((s) => s.columns) : columns;
  const { hasOptionColumn, hasAnswerColumn, hasResponseColumn, hasResponseQuestionOptionColumn } =
    useResolvedColumns(unionColumns, isBasicDetails);

  const {
    selections, setSelections,
    answers, setAnswers,
    responses, setResponses,
    responseOptionSelections, setResponseOptionSelections,
    productSelections, setProductSelections,
    dateSelections, setDateSelections,
    helpers, setHelpers,
    totals, addCalculatedHelper, removeCalculatedHelper, validateCalculatedValue,
    subSelections, subAnswers, subResponses,
    setSubSelection, setSubAnswer, setSubResponse,
    errors, helperErrors, clearError, clearHelperError,
    validate, getAnswers,
  } = useValidateTemplateAnswers({
    questions: allQuestions, hasOptionColumn, hasAnswerColumn, hasResponseColumn,
    hasResponseQuestionOptionColumn,
    isBasicDetails, isReconSheet, savedAnswers, savedSubAnswers,
  });

  // SAP auto-fill: in Basic Details, the editable INSP_LOT question drives a
  // SAP lookup on blur that fills every other mapped answer from the response.
  const { sapTriggerKey, fetchFromSap, sapLoading, sapError } = useSetSapAnswers({
    questions: allQuestions, isBasicDetails, answers, setAnswers,
  });

  // Product master options for "Masters" (Product Master) questions — the
  // OPTION column renders a product dropdown for those. Loaded only when the
  // stage actually has a Masters question.
  const hasMasters = allQuestions.some((q) => q.answer_type === 'Masters');
  const { data: productsData } = useProducts(hasMasters ? { limit: 500 } : undefined);
  const productOptions = (productsData?.items ?? []).map(
    (p: { id: string | number; product_name: string }) => ({ label: p.product_name, value: Number(p.id) })
  );
  // product id -> storage conditions, for auto-filling has_associated_master
  // questions when a product is picked.
  const storageByProductId = new Map<number, string>(
    (productsData?.items ?? []).map(
      (p: { id: string | number; storage_conditions?: string }) => [Number(p.id), p.storage_conditions ?? '']
    )
  );
  // The grid rows (keyed by stage_question_mapping_id) whose question has
  // has_associated_master = true — their answer is the selected product's
  // storage conditions.
  const associatedMasterKeys = allQuestions
    .filter((q) => q.has_associated_master)
    .map((q) => q.stage_question_mapping_id);
  /** Pick a product on a Masters row: record the selection and auto-fill any
   * has_associated_master question on THIS stage with the product's storage
   * conditions. (The Calculate_SampleConsumed total lives on the Test stage —
   * a different grid — so it's computed on the backend at submit, not here.) */
  const onProductPicked = (key: number, productId: number | null) => {
    setProductSelections((prev) => ({ ...prev, [key]: productId }));

    if (associatedMasterKeys.length > 0) {
      const storage = productId != null ? (storageByProductId.get(productId) ?? '') : '';
      setAnswers((prev) => {
        const next = { ...prev };
        for (const k of associatedMasterKeys) next[k] = storage;
        return next;
      });
    }
  };

  // Per-question approval remarks (mirrors the stage approval remark flow): the
  // current user may act while the stage is fillable (analyst) OR pending
  // approval (approver) — not on Basic Details. Only the first un-acted label
  // per question is editable, resolved inside the hook.
  const isPendingApproval = stageStatus === 'Pending' && !isBasicDetails;
  const canActApprovals = canAdd || isPendingApproval;
  const { data: remarksData } = useRemarks();
  const remarkOptions = (remarksData?.items ?? []).map(
    (r: { id: string | number; remark: string }) => ({ label: r.remark, value: Number(r.id), isOthers: r.remark === OTHERS_REMARK })
  );
  const remarkLabelById = new Map<number, string>(
    (remarksData?.items ?? []).map((r: { id: string | number; remark: string }) => [Number(r.id), r.remark])
  );
  const qApprovals = useQuestionApprovals({
    questions: allQuestions,
    canAct: canActApprovals,
    mappings: questionApprovalMappings,
    sqmByQuestionAnswerId,
    remarkOptions,
  });

  const subAccess: SubAnswerAccess = {
    getSelection: (p, s) => subSelections[`${p}:${s}`] ?? null,
    getAnswer: (p, s) => subAnswers[`${p}:${s}`] || '',
    getResponse: (p, s) => subResponses[`${p}:${s}`] || '',
    setSelection: setSubSelection,
    setAnswer: setSubAnswer,
    setResponse: setSubResponse,
  };

  const approvalAccess: QuestionApprovalAccess = {
    canAct: canActApprovals,
    remarkOptions,
    remarkLabelById,
    userNameById,
    getPick: qApprovals.getPick,
    getPickText: qApprovals.getPickText,
    setPick: qApprovals.setPick,
    setPickText: qApprovals.setPickText,
    getActed: qApprovals.getActed,
    isActed: qApprovals.isActed,
    getEditableLabelId: qApprovals.getEditableLabelId,
    getError: qApprovals.getError,
  };

  // The grid's validate() also enforces the per-question approval remarks, so
  // the existing submit flow (which calls snipRef.validate()) covers them.
  const validateAll = (): boolean => {
    const answersOk = validate();
    const approvalsOk = qApprovals.validate();
    return answersOk && approvalsOk;
  };

  return {
    allQuestions,
    canAdd,
    isBasicDetails,
    selections, setSelections,
    answers, setAnswers,
    responses, setResponses,
    responseOptionSelections, setResponseOptionSelections,
    productSelections, setProductSelections, onProductPicked, productOptions,
    dateSelections, setDateSelections,
    helpers, setHelpers,
    totals, addCalculatedHelper, removeCalculatedHelper, validateCalculatedValue,
    errors, helperErrors, clearError, clearHelperError,
    sapTriggerKey, fetchFromSap, sapLoading, sapError,
    subAccess, approvalAccess,
    validateAll, getAnswers,
    getQuestionApprovals: qApprovals.getQuestionApprovals,
  };
};
