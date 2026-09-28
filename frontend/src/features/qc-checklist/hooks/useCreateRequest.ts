/**
 * useCreateRequest — data loading and submission for CreateRequestPage.
 *
 * Owns:
 *  - the selected format and its checklist preview (GET /qc-checklist/preview)
 *  - each stage's Template Studio column layout, fetched alongside the
 *    preview (best-effort — a format with no layout configured yet is a
 *    normal state, not an error, since the hardcoded Snips still render)
 *  - which stages are expanded on the canvas
 *  - submit / save-as-draft for the current Initial stage, reading answers
 *    off whichever Snip ref is mounted for it
 *
 * CreateRequestPage stays composition + JSX only; this hook is the page's
 * "controller".
 */

import { useRef, useState } from 'react';
import { templateApi, type TemplateColumnResponse } from '@features/template-studio';
import { qcChecklistApi, type SubmitStageAnswerInput } from '../api/qcChecklistApi';
import type { ChecklistPreview } from '../models/ChecklistPreview';

export interface SnipHandle {
  validate: () => boolean;
  getAnswers: () => SubmitStageAnswerInput[];
}

export interface UseCreateRequestResult {
  loading: boolean;
  preview: ChecklistPreview | null;
  expandedStages: Record<number, boolean>;
  stageColumns: Record<number, TemplateColumnResponse[]>;
  snipRefs: React.RefObject<Record<number, SnipHandle | null>>;
  handleFormatChange: (formatId: number | null) => Promise<void>;
  toggleStage: (fsmId: number) => void;
  handleSubmit: () => Promise<void>;
  handleSaveAsDraft: () => Promise<void>;
}

export interface UseCreateRequestOptions {
  onError: (detail: string) => void;
  onSubmitSuccess: () => void;
  onDraftSuccess: () => void;
}

export const useCreateRequest = ({
  onError,
  onSubmitSuccess,
  onDraftSuccess,
}: UseCreateRequestOptions): UseCreateRequestResult => {
  const [loading, setLoading] = useState(false);
  const [preview, setPreview] = useState<ChecklistPreview | null>(null);
  const [expandedStages, setExpandedStages] = useState<Record<number, boolean>>({});
  const [stageColumns, setStageColumns] = useState<Record<number, TemplateColumnResponse[]>>({});
  const snipRefs = useRef<Record<number, SnipHandle | null>>({});

  const handleFormatChange = async (formatId: number | null) => {
    if (!formatId) {
      setPreview(null);
      setExpandedStages({});
      setStageColumns({});
      return;
    }
    setLoading(true);
    setPreview(null);
    setExpandedStages({});
    setStageColumns({});
    try {
      const data = await qcChecklistApi.getPreview(formatId);
      setPreview(data);

      // Fetch each stage's configured column layout from Template Studio in
      // parallel. Best-effort per stage — one stage's layout fetch failing
      // shouldn't block the rest.
      const columnsByStage = await Promise.all(
        data.stages.map(async (stage) => {
          try {
            const columns = await templateApi.listColumnsForStage(stage.format_stage_mapping_id);
            return [stage.format_stage_mapping_id, columns] as const;
          } catch {
            return [stage.format_stage_mapping_id, []] as const;
          }
        })
      );
      setStageColumns(Object.fromEntries(columnsByStage));
    } catch (e) {
      const detail = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      onError(detail || 'Failed to load checklist');
    } finally {
      setLoading(false);
    }
  };

  const toggleStage = (fsmId: number) => {
    setExpandedStages((prev) => ({ ...prev, [fsmId]: !prev[fsmId] }));
  };

  /** Submit or save-as-draft the current Initial stage's answers. */
  const submitCurrentStage = async (action: 'submit' | 'save_draft') => {
    if (!preview) return;
    const stage = preview.stages.find((s) => s.status === 'Initial');
    if (!stage) return;

    const ref = snipRefs.current[stage.format_stage_mapping_id];
    const answers = ref?.getAnswers() ?? [];

    await qcChecklistApi.submitStage({
      checklist_request_id: null,
      format_id: preview.format_id,
      checklist_stage_id: null,
      format_stage_mapping_id: stage.format_stage_mapping_id,
      action,
      remark_id: null,
      remark_text: '',
      answers: answers.map((a) => ({
        stage_question_mapping_id: a.stage_question_mapping_id,
        question_id: a.question_id,
        textbox_value: a.textbox_value,
        question_option_id: a.question_option_id,
        response_answer: a.response_answer,
        product_id: a.product_id ?? null,
        date_time: a.date_time ?? null,
        helpers: a.helpers.length > 0 ? a.helpers : [],
      })),
    });
  };

  const handleSubmit = async () => {
    // Validate every mounted stage snip before submitting.
    let allValid = true;
    for (const key of Object.keys(snipRefs.current)) {
      const ref = snipRefs.current[Number(key)];
      if (ref && !ref.validate()) allValid = false;
    }
    if (!allValid) {
      onError('Please fill all required fields.');
      return;
    }
    try {
      await submitCurrentStage('submit');
      onSubmitSuccess();
    } catch (e) {
      const detail = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      onError(detail || 'Submit failed');
    }
  };

  const handleSaveAsDraft = async () => {
    try {
      await submitCurrentStage('save_draft');
      onDraftSuccess();
    } catch (e) {
      const detail = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      onError(detail || 'Save failed');
    }
  };

  return {
    loading,
    preview,
    expandedStages,
    stageColumns,
    snipRefs,
    handleFormatChange,
    toggleStage,
    handleSubmit,
    handleSaveAsDraft,
  };
};
