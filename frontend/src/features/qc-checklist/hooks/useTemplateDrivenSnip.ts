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
  helpers: Record<number, string[]>;
  setHelpers: React.Dispatch<React.SetStateAction<Record<number, string[]>>>;
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
  // answer hook validates/returns the whole stage.
  const allQuestions: QuestionAnswerPreview[] = hasSection
    ? sections.flatMap((s) => s.questions)
    : questions;

  // Column-type flags from the union of stage + section columns.
  const unionColumns = hasSection ? sections.flatMap((s) => s.columns) : columns;
  const { hasOptionColumn, hasAnswerColumn, hasResponseColumn } = useResolvedColumns(unionColumns, isBasicDetails);

  const {
    selections, setSelections,
    answers, setAnswers,
    responses, setResponses,
    helpers, setHelpers,
    subSelections, subAnswers, subResponses,
    setSubSelection, setSubAnswer, setSubResponse,
    errors, helperErrors, clearError, clearHelperError,
    validate, getAnswers,
  } = useValidateTemplateAnswers({
    questions: allQuestions, hasOptionColumn, hasAnswerColumn, hasResponseColumn,
    isBasicDetails, savedAnswers, savedSubAnswers,
  });

  // SAP auto-fill: in Basic Details, the editable INSP_LOT question drives a
  // SAP lookup on blur that fills every other mapped answer from the response.
  const { sapTriggerKey, fetchFromSap, sapLoading, sapError } = useSetSapAnswers({
    questions: allQuestions, isBasicDetails, answers, setAnswers,
  });

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
    getSelection: (p, s) => subSelections[`${p}:${s}`],
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
    helpers, setHelpers,
    errors, helperErrors, clearError, clearHelperError,
    sapTriggerKey, fetchFromSap, sapLoading, sapError,
    subAccess, approvalAccess,
    validateAll, getAnswers,
    getQuestionApprovals: qApprovals.getQuestionApprovals,
  };
};
