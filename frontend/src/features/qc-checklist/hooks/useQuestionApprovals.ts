/**
 * useQuestionApprovals — per-question approval remark state for the fill grid.
 *
 * Mirrors the stage approval remark flow (ApprovalSnip) but per question: for
 * each approvable question + its approval labels, holds the current user's
 * remark pick, pre-fills already-acted picks from loaded mappings, exposes the
 * acted/read-only state, and produces the submit payload (one entry per
 * label the user acted on this time).
 *
 * The grid keys everything by stage_question_mapping_id; loaded mappings are
 * keyed by question_answer_id, so a question_answer_id -> sqm_id map (built
 * from the loaded answers) is used to attach a question's prior mappings.
 */

import { useMemo, useState } from 'react';
import type { QuestionAnswerPreview } from '../models/TemplateTypes';
import type { ApprovalLabelMappingResponse, QuestionApprovalInput } from '../api/qcChecklistApi';

/** Composite key for one question+label pick. */
const pickKey = (sqmId: number, labelId: number) => `${sqmId}:${labelId}`;

export interface UseQuestionApprovalsOptions {
  /** Every question in the stage (flattened across sections). */
  questions: QuestionAnswerPreview[];
  /** True while the stage is fillable/approvable for the current user. */
  canAct: boolean;
  /** Loaded per-question mappings for this request (keyed by question_answer_id). */
  mappings?: ApprovalLabelMappingResponse[];
  /** question_answer_id -> stage_question_mapping_id, from the loaded answers. */
  sqmByQuestionAnswerId?: Record<number, number>;
  /** Remark options (to know which pick is "Others" → requires free-text). */
  remarkOptions?: { value: number; isOthers: boolean }[];
}

export interface ActedInfo {
  remark_id: number | null;
  remark: string;
  user_id: number | null;
  date_of_action: string | null;
}

export interface UseQuestionApprovalsResult {
  /** Inline error for a question+label's remark (set by validate), or undefined. */
  getError: (sqmId: number, labelId: number) => string | undefined;
  /** Current remark pick (remark_id) for a question+label, or undefined. */
  getPick: (sqmId: number, labelId: number) => number | null | undefined;
  /** Current free-text (for "Others") for a question+label. */
  getPickText: (sqmId: number, labelId: number) => string;
  setPick: (sqmId: number, labelId: number, remarkId: number | null) => void;
  setPickText: (sqmId: number, labelId: number, text: string) => void;
  /** Prior acted mapping for a question+label (read-only display), if any. */
  getActed: (sqmId: number, labelId: number) => ActedInfo | undefined;
  /** True when a question+label was already acted on (and is read-only now). */
  isActed: (sqmId: number, labelId: number) => boolean;
  /** The one label currently editable for a question — the first un-acted
   * label (in config order), mirroring the stage approval flow. Null when the
   * user can't act or every label is acted. */
  getEditableLabelId: (sqmId: number, orderedLabelIds: number[]) => number | null;
  /** Validate: every approvable question's currently-editable label must have a
   * remark chosen (and free-text when "Others"). Sets inline errors; returns false
   * if any is missing. Mirrors ApprovalSnip.validateRemark but per question. */
  validate: () => boolean;
  /** Build the submit payload — one entry per label the user picked a remark for. */
  getQuestionApprovals: () => QuestionApprovalInput[];
}

export const useQuestionApprovals = ({
  questions,
  canAct,
  mappings = [],
  sqmByQuestionAnswerId = {},
  remarkOptions = [],
}: UseQuestionApprovalsOptions): UseQuestionApprovalsResult => {
  const isOthersValue = (remarkId: number | null | undefined) =>
    remarkOptions.find((o) => o.value === remarkId)?.isOthers ?? false;
  const [picks, setPicks] = useState<Record<string, number | null>>({});
  const [pickTexts, setPickTexts] = useState<Record<string, string>>({});
  const [errors, setErrors] = useState<Record<string, string>>({});

  // Prior acted mappings, keyed by `${sqmId}:${labelId}` (resolved via the
  // question_answer_id -> sqm map).
  const actedByKey = useMemo(() => {
    const out: Record<string, ActedInfo> = {};
    for (const m of mappings) {
      if (m.question_answer_id == null || !m.date_of_action) continue;
      const sqmId = sqmByQuestionAnswerId[m.question_answer_id];
      if (sqmId == null) continue;
      out[pickKey(sqmId, m.approval_label_id)] = {
        remark_id: m.remark_id,
        remark: m.remark,
        user_id: m.user_id,
        date_of_action: m.date_of_action,
      };
    }
    return out;
  }, [mappings, sqmByQuestionAnswerId]);

  const getActed = (sqmId: number, labelId: number) => actedByKey[pickKey(sqmId, labelId)];
  const isActed = (sqmId: number, labelId: number) => !!actedByKey[pickKey(sqmId, labelId)];

  // Only the first un-acted label (in config order) is editable at a time —
  // so "Analysed By" is editable at fill, and once acted "Approved By" becomes
  // the next editable one for the approver. Mirrors ApprovalSnip's editableLabelId.
  const getEditableLabelId = (sqmId: number, orderedLabelIds: number[]): number | null => {
    if (!canAct) return null;
    return orderedLabelIds.find((id) => !isActed(sqmId, id)) ?? null;
  };

  const getPick = (sqmId: number, labelId: number) => picks[pickKey(sqmId, labelId)];
  const getPickText = (sqmId: number, labelId: number) => pickTexts[pickKey(sqmId, labelId)] ?? '';
  const getError = (sqmId: number, labelId: number) => errors[pickKey(sqmId, labelId)];
  const clearError = (key: string) =>
    setErrors((e) => { if (!e[key]) return e; const n = { ...e }; delete n[key]; return n; });
  const setPick = (sqmId: number, labelId: number, remarkId: number | null) => {
    setPicks((p) => ({ ...p, [pickKey(sqmId, labelId)]: remarkId }));
    clearError(pickKey(sqmId, labelId));
  };
  const setPickText = (sqmId: number, labelId: number, text: string) => {
    setPickTexts((p) => ({ ...p, [pickKey(sqmId, labelId)]: text }));
    clearError(pickKey(sqmId, labelId));
  };

  /** Every approvable question's currently-editable label must have a remark
   * (and free-text when "Others"). */
  const validate = (): boolean => {
    if (!canAct) return true;
    const next: Record<string, string> = {};
    let ok = true;
    for (const q of questions) {
      const labels = q.approval_labels ?? [];
      if (labels.length === 0) continue;
      const sqmId = q.stage_question_mapping_id;
      const orderedIds = labels.map((l) => l.approval_label_id);
      const editableId = orderedIds.find((id) => !isActed(sqmId, id));
      if (editableId == null) continue;
      const key = pickKey(sqmId, editableId);
      const remarkId = picks[key];
      if (remarkId == null) {
        next[key] = 'Please select a remark.';
        ok = false;
      } else if (isOthersValue(remarkId) && !(pickTexts[key] ?? '').trim()) {
        next[key] = 'Please enter a remark.';
        ok = false;
      }
    }
    setErrors(next);
    return ok;
  };

  const getQuestionApprovals = (): QuestionApprovalInput[] => {
    if (!canAct) return [];
    const out: QuestionApprovalInput[] = [];
    for (const q of questions) {
      const sqmId = q.stage_question_mapping_id;
      for (const label of q.approval_labels ?? []) {
        const labelId = label.approval_label_id;
        // Skip labels already acted on (read-only) and labels the user left blank.
        if (isActed(sqmId, labelId)) continue;
        const remarkId = picks[pickKey(sqmId, labelId)];
        if (remarkId == null) continue;
        out.push({
          stage_question_mapping_id: sqmId,
          approval_label_id: labelId,
          remark_id: remarkId,
          remark_text: pickTexts[pickKey(sqmId, labelId)] ?? '',
        });
      }
    }
    return out;
  };

  return {
    getError, getPick, getPickText, setPick, setPickText,
    getActed, isActed, getEditableLabelId, validate, getQuestionApprovals,
  };
};
