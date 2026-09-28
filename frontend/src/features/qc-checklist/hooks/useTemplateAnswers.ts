/**
 * useTemplateAnswers — per-row answer state and validation for TemplateDrivenSnip.
 *
 * Owns the five pieces of state a row can carry (selected option(s), typed
 * answer, response radio, "+ Add" helper text boxes, and field-level
 * errors), plus the validate()/getAnswers() logic CreateRequestPage's
 * submit/draft flow calls through the component's ref handle.
 */

import { useState } from 'react';
import type { QuestionAnswerPreview, TemplateAnswer } from '../models/TemplateTypes';

export type RowErrors = { options?: string; answer?: string; response?: string };

export interface UseTemplateAnswersOptions {
  questions: QuestionAnswerPreview[];
  hasOptionColumn: boolean;
  hasAnswerColumn: boolean;
  hasResponseColumn: boolean;
  isBasicDetails: boolean;
}

export interface UseTemplateAnswersResult {
  selections: Record<number, unknown>;
  setSelections: React.Dispatch<React.SetStateAction<Record<number, unknown>>>;
  answers: Record<number, string>;
  setAnswers: React.Dispatch<React.SetStateAction<Record<number, string>>>;
  responses: Record<number, string>;
  setResponses: React.Dispatch<React.SetStateAction<Record<number, string>>>;
  helpers: Record<number, string[]>;
  setHelpers: React.Dispatch<React.SetStateAction<Record<number, string[]>>>;
  errors: Record<number, RowErrors>;
  clearError: (key: number, field: keyof RowErrors) => void;
  validate: () => boolean;
  getAnswers: () => TemplateAnswer[];
}

export const useTemplateAnswers = ({
  questions,
  hasOptionColumn,
  hasAnswerColumn,
  hasResponseColumn,
  isBasicDetails,
}: UseTemplateAnswersOptions): UseTemplateAnswersResult => {
  const [selections, setSelections] = useState<Record<number, unknown>>({});
  const [answers, setAnswers] = useState<Record<number, string>>({});
  const [responses, setResponses] = useState<Record<number, string>>({});
  const [helpers, setHelpers] = useState<Record<number, string[]>>({});
  const [errors, setErrors] = useState<Record<number, RowErrors>>({});

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

  const validate = (): boolean => {
    const newErrors: Record<number, RowErrors> = {};
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

      if (rowErrors.options || rowErrors.answer || rowErrors.response) {
        newErrors[key] = rowErrors;
      }
    }

    setErrors(newErrors);
    return isValid;
  };

  const getAnswers = (): TemplateAnswer[] =>
    questions.map((row) => {
      const key = row.stage_question_mapping_id;
      return {
        stage_question_mapping_id: key,
        question_id: row.question_id,
        textbox_value: answers[key] || '',
        question_option_id: typeof selections[key] === 'number' ? (selections[key] as number) : null,
        response_answer: responses[key] || '',
        helpers: helpers[key] || [],
      };
    });

  return {
    selections, setSelections,
    answers, setAnswers,
    responses, setResponses,
    helpers, setHelpers,
    errors, clearError,
    validate, getAnswers,
  };
};
