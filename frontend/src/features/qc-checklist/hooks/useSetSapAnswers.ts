/**
 * useSetSapAnswers — AQL Basic Details SAP auto-fill.
 *
 * In Basic Details, one editable question is mapped to the SAP field that
 * drives the lookup (INSP_LOT). When its answer is entered, this hook looks up
 * SAP by that value and fills every other Basic Details answer whose question
 * is mapped to a SAP field present in the response — matched 1:1 by
 * sap_field_name against the response's T_OUTPUT.item keys.
 *
 * The component only needs to wire fetchFromSap() to the trigger input's blur
 * and render sapError / sapLoading; all the lookup + matching lives here.
 */

import { useRef, useState } from 'react';
import axios from 'axios';
import type { QuestionAnswerPreview } from '../models/TemplateTypes';
import { useSapQcChecklist } from '../../service-menu/hooks/useSap';

/** The SAP field whose question drives the lookup — its entered answer is the
 * I_INSP search param. All other Basic Details answers are filled from the
 * response, matched by each question's own sap_field_name. */
const SAP_TRIGGER_FIELD = 'INSP_LOT';

/** SAP returns the vendor batch zero-padded (e.g. "0000012345"); the form
 * expects it without the leading zeros. */
const VENDOR_BATCH_FIELD = 'VEND_BATCH';

/** Normalise a SAP value for display in the answer box. VEND_BATCH is stripped
 * of leading zeros; everything else is used as-is. */
const normalizeSapValue = (field: string, raw: string): string => {
  if (field === VENDOR_BATCH_FIELD) {
    // Drop leading zeros but never leave an empty string for an all-zero value.
    const stripped = raw.replace(/^0+/, '');
    return stripped === '' ? '0' : stripped;
  }
  return raw;
};

export interface UseSetSapAnswersOptions {
  /** Every question in the stage (flattened across sections). */
  questions: QuestionAnswerPreview[];
  /** True only for the Basic Details stage — the only one carrying SAP maps. */
  isBasicDetails: boolean;
  /** Current answer values, keyed by stage_question_mapping_id. */
  answers: Record<number, string>;
  /** Setter for the answer map (used to write the auto-filled values). */
  setAnswers: React.Dispatch<React.SetStateAction<Record<number, string>>>;
}

export interface UseSetSapAnswersResult {
  /** stage_question_mapping_id of the editable INSP_LOT question, or null when
   * this stage has no SAP trigger (non-Basic-Details, or not mapped). */
  sapTriggerKey: number | null;
  /** Run the lookup for the trigger's current value and auto-fill the rest. */
  fetchFromSap: () => Promise<void>;
  /** True while the SAP request is in flight. */
  sapLoading: boolean;
  /** User-facing error (permission denied / lookup failed), or null. */
  sapError: string | null;
}

export const useSetSapAnswers = ({
  questions,
  isBasicDetails,
  answers,
  setAnswers,
}: UseSetSapAnswersOptions): UseSetSapAnswersResult => {
  const sapLookup = useSapQcChecklist();
  const [sapError, setSapError] = useState<string | null>(null);
  // Last value we actually looked up, so a blur with an unchanged value
  // (e.g. tabbing through) doesn't re-hit SAP.
  const lastSapLookupRef = useRef<string | null>(null);

  const sapTriggerKey = isBasicDetails
    ? questions.find(
        (q) => q.sap_field_name === SAP_TRIGGER_FIELD && q.is_editable !== false
      )?.stage_question_mapping_id ?? null
    : null;

  const fetchFromSap = async (): Promise<void> => {
    if (sapTriggerKey == null) return;
    const inspLot = (answers[sapTriggerKey] || '').trim();
    // Nothing entered, or same value already looked up — do nothing.
    if (!inspLot || inspLot === lastSapLookupRef.current) return;
    lastSapLookupRef.current = inspLot;
    setSapError(null);
    try {
      const { item } = await sapLookup.mutateAsync(inspLot);
      setAnswers((prev) => {
        const next = { ...prev };
        for (const q of questions) {
          const field = q.sap_field_name;
          // Skip the trigger itself (keep what the user typed) and any
          // question without a SAP mapping or without a value in the response.
          if (!field || q.stage_question_mapping_id === sapTriggerKey) continue;
          const value = item[field];
          if (value != null && value !== '') {
            next[q.stage_question_mapping_id] = normalizeSapValue(field, String(value));
          }
        }
        return next;
      });
    } catch (err) {
      // Allow a retry with the same value after a failure.
      lastSapLookupRef.current = null;
      // A 403 from the services.sap permission gate means the user isn't
      // authorized to call SAP — surface that distinctly from a lookup error.
      const status = axios.isAxiosError(err) ? err.response?.status : undefined;
      setSapError(
        status === 403
          ? 'Permission denied: you are not authorized to fetch from SAP.'
          : 'SAP lookup failed. Check the value and try again.'
      );
    }
  };

  return { sapTriggerKey, fetchFromSap, sapLoading: sapLookup.isPending, sapError };
};
