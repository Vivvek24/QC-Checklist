/**
 * useQuestionChoices — the list of questions available to pick on the design
 * canvas: the FULL question master (so this page can replace the old mapping
 * pages), enriched with the richer preview data (options, aql_limit,
 * sub-questions) for questions already mapped to this format.
 */

import { useMemo } from 'react';
import type { ChecklistPreview } from '../models/Preview';
import type { QuestionChoice } from '../components/ConfigTable';

/** Minimal shape of a question master row, as returned by useQuestions(). */
export interface QuestionMasterRow {
  id: number | string;
  title: string;
  answer_type: string;
  has_text_box: boolean;
  has_multiple_text_box: boolean;
  has_sub_question: boolean;
  master_type?: string | null;
}

export const useQuestionChoices = (
  preview: ChecklistPreview | undefined,
  questionsData: { items: QuestionMasterRow[] } | undefined
): QuestionChoice[] =>
  useMemo(() => {
    // Preview questions, keyed by id, carry the resolved options/sub-questions.
    const previewById = new Map<number, QuestionChoice>();
    for (const stage of preview?.stages ?? []) {
      const all = [...stage.questions, ...stage.sections.flatMap((sec) => sec.questions)];
      for (const q of all) {
        if (!previewById.has(q.question_id)) {
          previewById.set(q.question_id, {
            id: q.question_id,
            title: q.question_title,
            answerType: q.answer_type,
            hasTextBox: q.has_text_box,
            hasMultipleTextBox: q.has_multiple_text_box,
            hasSubQuestion: q.has_sub_question,
            masterType: q.master_type ?? null,
            options: q.options ?? [],
            aqlLimit: q.aql_limit ?? '',
            subQuestions: (q.sub_questions ?? []).map((sub) => ({
              id: sub.question_id,
              title: sub.question_title,
              answerType: sub.answer_type,
              hasTextBox: sub.has_text_box,
              hasMultipleTextBox: sub.has_multiple_text_box,
              options: sub.options ?? [],
            })),
          });
        }
      }
    }

    // Start from the full master; prefer the preview entry when available.
    const result: QuestionChoice[] = [];
    const seen = new Set<number>();
    for (const q of questionsData?.items ?? []) {
      const id = Number(q.id);
      seen.add(id);
      const fromPreview = previewById.get(id);
      result.push(
        fromPreview ?? {
          id,
          title: q.title,
          answerType: q.answer_type,
          hasTextBox: q.has_text_box,
          hasMultipleTextBox: q.has_multiple_text_box,
          hasSubQuestion: q.has_sub_question,
          masterType: q.master_type ?? null,
          // Options / sub-questions are not on the base master list; they are
          // resolved from preview once the question is mapped. Empty here.
          options: [],
          aqlLimit: '',
          subQuestions: [],
        }
      );
    }
    // Include any preview-only questions not in the current master page.
    for (const [id, choice] of previewById) {
      if (!seen.has(id)) result.push(choice);
    }
    return result.sort((a, b) => a.title.localeCompare(b.title));
  }, [preview, questionsData]);
