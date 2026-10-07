/**
 * useValidateTemplateAnswers — per-row answer state and validation for TemplateDrivenSnip.
 *
 * Owns the five pieces of state a row can carry (selected option(s), typed
 * answer, response radio, "+ Add" helper text boxes, and field-level
 * errors), plus the validate()/getAnswers() logic CreateRequestPage's
 * submit/draft flow calls through the component's ref handle.
 */

import { useEffect, useState } from 'react';
import type { QuestionAnswerPreview, TemplateAnswer } from '../models/TemplateTypes';

export type RowErrors = { options?: string; answer?: string; response?: string };

/** Pre-loaded saved answer for a question row (keyed by stage_question_mapping_id). */
export interface SavedAnswer {
  textbox_value: string;
  question_option_id: number | null;
  response_answer: string;
}

export interface UseValidateTemplateAnswersOptions {
  questions: QuestionAnswerPreview[];
  hasOptionColumn: boolean;
  hasAnswerColumn: boolean;
  hasResponseColumn: boolean;
  isBasicDetails: boolean;
  /** Pre-loaded saved answers keyed by stage_question_mapping_id (for read-only view). */
  savedAnswers?: Record<number, SavedAnswer>;
}

export interface UseValidateTemplateAnswersResult {
  selections: Record<number, unknown>;
  setSelections: React.Dispatch<React.SetStateAction<Record<number, unknown>>>;
  answers: Record<number, string>;
  setAnswers: React.Dispatch<React.SetStateAction<Record<number, string>>>;
  responses: Record<number, string>;
  setResponses: React.Dispatch<React.SetStateAction<Record<number, string>>>;
  helpers: Record<number, string[]>;
  setHelpers: React.Dispatch<React.SetStateAction<Record<number, string[]>>>;
  errors: Record<number, RowErrors>;
  /** Per-row, per-helper-index inline errors for the "+ Add" helper boxes. */
  helperErrors: Record<number, (string | undefined)[]>;
  clearError: (key: number, field: keyof RowErrors) => void;
  /** Clear the inline error for one helper box as the user edits it. */
  clearHelperError: (key: number, idx: number) => void;
  validate: () => boolean;
  getAnswers: () => TemplateAnswer[];
}

/** Only letters, digits, hyphen, underscore, slash and dot are allowed in a
 * helper value (no spaces or other special characters). */
const HELPER_ALLOWED = /^[A-Za-z0-9\-_/.]+$/;

export const useValidateTemplateAnswers = ({
  questions,
  hasOptionColumn,
  hasAnswerColumn,
  hasResponseColumn,
  isBasicDetails,
  savedAnswers,
}: UseValidateTemplateAnswersOptions): UseValidateTemplateAnswersResult => {
  const [selections, setSelections] = useState<Record<number, unknown>>({});
  const [answers, setAnswers] = useState<Record<number, string>>({});
  const [responses, setResponses] = useState<Record<number, string>>({});
  const [helpers, setHelpers] = useState<Record<number, string[]>>({});
  const [errors, setErrors] = useState<Record<number, RowErrors>>({});
  const [helperErrors, setHelperErrors] = useState<Record<number, (string | undefined)[]>>({});

  // Seed state from pre-loaded saved answers (resuming / viewing a submitted
  // stage). Runs when the saved answers arrive so already-filled stages render
  // their persisted values.
  useEffect(() => {
    if (!savedAnswers) return;
    // Multi-select questions hold their value as an array, not a scalar —
    // PrimeReact's MultiSelect calls .slice() on it and crashes otherwise.
    const answerTypeByKey = new Map<number, string>(
      questions.map((q) => [q.stage_question_mapping_id, q.answer_type])
    );
    const nextSelections: Record<number, unknown> = {};
    const nextAnswers: Record<number, string> = {};
    const nextResponses: Record<number, string> = {};
    for (const [k, sa] of Object.entries(savedAnswers)) {
      const key = Number(k);
      if (sa.question_option_id != null) {
        const isMulti = answerTypeByKey.get(key) === 'Dropdown (multi select)';
        nextSelections[key] = isMulti ? [sa.question_option_id] : sa.question_option_id;
      }
      if (sa.textbox_value) nextAnswers[key] = sa.textbox_value;
      if (sa.response_answer) nextResponses[key] = sa.response_answer;
    }
    setSelections(nextSelections);
    setAnswers(nextAnswers);
    setResponses(nextResponses);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [savedAnswers]);

  const clearError = (key: number, field: keyof RowErrors) =>
    setErrors((prev) => {
      const next = { ...prev };
      if (next[key]) {
        const { [field]: _removed, ...rest } = next[key]!;
        if (Object.keys(rest).length === 0) delete next[key];
        else next[key] = rest;
      }
      return next;
    });

  const clearHelperError = (key: number, idx: number) =>
    setHelperErrors((prev) => {
      if (!prev[key] || prev[key][idx] === undefined) return prev;
      const arr = [...prev[key]];
      arr[idx] = undefined;
      return { ...prev, [key]: arr };
    });

  const validate = (): boolean => {
    const newErrors: Record<number, RowErrors> = {};
    const newHelperErrors: Record<number, (string | undefined)[]> = {};
    let isValid = true;

    for (const row of questions) {
      const key = row.stage_question_mapping_id;
      const rowErrors: RowErrors = {};

      if (hasOptionColumn) {
        if (row.answer_type === 'Dropdown (single select)') {
          if (!selections[key]) {
            rowErrors.options = 'Choose one option above!';
            isValid = false;
          }
        } else if (row.answer_type === 'Dropdown (multi select)') {
          const value = selections[key];
          if (!value || (Array.isArray(value) && value.length === 0)) {
            rowErrors.options = 'Choose one/multiple option(s) above!';
            isValid = false;
          }
        }
      }

      const showTextBox = row.answer_type === 'Text Box' || (row.answer_type !== 'None' && row.has_text_box);
      if (hasAnswerColumn && showTextBox) {
        const value = answers[key];
        if (!value || !value.trim()) {
          rowErrors.answer = 'Please enter the value.';
          isValid = false;
        } else if (value.includes(' ') && row.answer_type === 'Text Box') {
          rowErrors.answer = 'Spaces not allowed!';
          isValid = false;
        }
      }

      if (hasResponseColumn && !isBasicDetails) {
        if (!responses[key]) {
          rowErrors.response = 'Select a response!';
          isValid = false;
        }
      }

      // Helper ("+ Add") boxes: each is required, must contain no special
      // characters/spaces, and must not duplicate the main answer or another
      // helper on the same row.
      const rowHelpers = helpers[key] || [];
      if (rowHelpers.length > 0) {
        const mainValue = (answers[key] || '').trim();
        const perHelper: (string | undefined)[] = [];
        const seen = new Set<string>();
        rowHelpers.forEach((raw, idx) => {
          const value = (raw || '').trim();
          let err: string | undefined;
          if (!value) {
            err = 'Please enter the value.';
          } else if (!HELPER_ALLOWED.test(value)) {
            err = 'Special characters not allowed!';
          } else if (value.toUpperCase() === mainValue.toUpperCase()) {
            err = 'Cannot be same as the answer above.';
          } else if (seen.has(value.toUpperCase())) {
            err = 'Duplicate value.';
          }
          if (!err) seen.add(value.toUpperCase());
          else isValid = false;
          perHelper[idx] = err;
        });
        if (perHelper.some((e) => e !== undefined)) {
          newHelperErrors[key] = perHelper;
        }
      }

      if (rowErrors.options || rowErrors.answer || rowErrors.response) {
        newErrors[key] = rowErrors;
      }
    }

    setErrors(newErrors);
    setHelperErrors(newHelperErrors);
    return isValid;
  };

  const getAnswers = (): TemplateAnswer[] =>
    questions.map((row) => {
      const key = row.stage_question_mapping_id;
      // Single-select → a number; multi-select → an array of numbers.
      const sel = selections[key];
      const optionId: number | null =
        typeof sel === 'number' ? sel :
        Array.isArray(sel) && sel.length > 0 ? sel[0] : null;
      return {
        stage_question_mapping_id: key,
        question_id: row.question_id,
        textbox_value: answers[key] || '',
        question_option_id: optionId,
        response_answer: responses[key] || '',
        helpers: helpers[key] || [],
      };
    });

  return {
    selections, setSelections,
    answers, setAnswers,
    responses, setResponses,
    helpers, setHelpers,
    errors, helperErrors, clearError, clearHelperError,
    validate, getAnswers,
  };
};
