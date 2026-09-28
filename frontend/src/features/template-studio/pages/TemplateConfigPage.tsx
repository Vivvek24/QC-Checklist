/**
 * TemplateConfigPage — Template Config for a format.
 *
 * Opened from the Formats View page with a :formatId. Renders the checklist
 * header (from /qc-checklist/preview) and the design canvas where the user
 * composes stages/sections and their column layouts.
 *
 * This page is composition + render only — data loading, question-choice
 * derivation, and persistence each live in their own hook (see ../hooks):
 *  - useTemplateConfigData: hydrates the canvas from what's already saved
 *  - useQuestionChoices: the question picker's options
 *  - useTemplateSave: the Save pipeline (rows/sections/columns) + deletions
 */

import { useMemo, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Skeleton } from 'primereact/skeleton';
import { Button } from 'primereact/button';
import { Tag } from 'primereact/tag';
import { Toast } from 'primereact/toast';
import { apiClient } from '@shared/services/apiClient';
import { ChecklistHeader } from '@features/qc-checklist/components/ChecklistHeader';
import { useSapFields } from '@features/masters/hooks/useSapFields';
import { useQuestions } from '@features/masters/hooks/useQuestions';
import { useStages } from '@features/masters/hooks/useStages';
import { CUSTOM_ANSWER_OPTIONS } from '@features/masters/constants';
import { useChecklistPreview } from '../hooks/useChecklistPreview';
import { useTemplateConfigData } from '../hooks/useTemplateConfigData';
import { useQuestionChoices } from '../hooks/useQuestionChoices';
import { useTemplateSave } from '../hooks/useTemplateSave';
import { StageConfig, type StageOption, type MappingContext } from '../components/StageConfig';
import type { DesignStage } from '../models/DesignSpec';
import { emptyStage } from '../models/DesignSpec';

export const TemplateConfigPage = () => {
  const { formatId: formatIdParam } = useParams<{ formatId?: string }>();
  const navigate = useNavigate();
  const { data: sapFieldsData } = useSapFields();
  const { data: stagesData } = useStages();

  const formatId = formatIdParam ? Number(formatIdParam) : null;
  const { data: preview, isLoading: previewLoading } = useChecklistPreview(formatId);
  const { data: questionsData } = useQuestions();

  const { stages, setStages, loadingConfig } = useTemplateConfigData(preview);
  const questionChoices = useQuestionChoices(preview, questionsData);

  // Format-level context passed to every stage/section table.
  const ctx: MappingContext = useMemo(
    () => ({
      formatType: preview?.format_type ?? '',
      hasDeclarationQuestion: preview?.has_declaration_question ?? false,
      sapFields: (sapFieldsData?.items ?? []).map((s) => ({
        id: Number(s.id),
        label: (s as { field_name?: string; name?: string }).field_name ?? (s as { name?: string }).name ?? '',
      })),
      customAnswerOptions: CUSTOM_ANSWER_OPTIONS,
    }),
    [preview, sapFieldsData]
  );

  // Stage dropdown lists every stage from the Stage master — not just ones
  // already mapped to this format. Stages already mapped (present in the
  // preview) carry their existing fsmId/approvalLabels/hasSection; a stage
  // picked that has never been mapped for this format has fsmId: null and
  // gets its format_stage_mapping row created automatically on Save.
  const stageOptions: StageOption[] = useMemo(() => {
    const mappedByStageId = new Map((preview?.stages ?? []).map((s) => [s.stage_id, s]));
    return (stagesData?.items ?? []).map((stage) => {
      const stageId = Number(stage.id);
      const mapped = mappedByStageId.get(stageId);
      return {
        fsmId: mapped?.format_stage_mapping_id ?? null,
        stageId,
        stageName: stage.stage_name,
        approvalLabels: (mapped?.approval_labels ?? []).map((a) => ({
          id: a.approval_label_id,
          label: a.label,
        })),
        hasSection: mapped?.has_section ?? false,
      };
    });
  }, [preview, stagesData]);

  const toast = useRef<Toast>(null);

  /** Persist has_section immediately — mirrors the Stage Question Mapping
   * page's toggle (PATCH /masters/format-stage-mappings/:id). */
  const toggleHasSection = async (fsmId: number, value: boolean) => {
    try {
      await apiClient.patch(`/masters/format-stage-mappings/${fsmId}`, { has_section: value });
    } catch {
      toast.current?.show({
        severity: 'error',
        summary: 'Could not update Has Section',
        detail: 'Please try again.',
        life: 4000,
      });
    }
  };

  const { saving, handleSaveAll, markRowDeleted, markSectionDeleted, markStageRemoved } = useTemplateSave({
    stages,
    setStages,
    formatId,
    onSuccess: () =>
      toast.current?.show({ severity: 'success', summary: 'Saved', detail: 'Template configuration saved.', life: 3000 }),
    onError: (detail) =>
      toast.current?.show({ severity: 'error', summary: 'Save failed', detail, life: 5000 }),
  });

  const addStage = () => setStages([...stages, emptyStage()]);
  const updateStage = (key: string, stage: DesignStage) =>
    setStages(stages.map((s) => (s.key === key ? stage : s)));
  const removeStage = (key: string) => {
    const stage = stages.find((s) => s.key === key);
    if (stage) {
      for (const row of stage.rows) {
        if (row.mappingId) markRowDeleted(row.mappingId);
      }
      for (const section of stage.sections) {
        markSectionDeleted(section);
      }
      markStageRemoved(stage.stageId);
    }
    setStages(stages.filter((s) => s.key !== key));
  };

  return (
    <div className="p-3 snip-page">
      <Toast ref={toast} />

      {/* Back link */}
      <div className="flex align-items-center justify-content-between gap-2 mb-3">
        <div className="flex align-items-center gap-2">
          <Button icon="pi pi-arrow-left" severity="secondary" text
            onClick={() => navigate('/masters/formats-view')} type="button" />
          <div>
            <h2 className="text-xl font-semibold text-900 m-0">Template Config</h2>
            <p className="text-600 mt-1 mb-0">Design the checklist column layout for this format</p>
          </div>
        </div>
        {formatId != null && (
          <Button
            label="Save Configuration"
            icon="pi pi-save"
            loading={saving}
            onClick={handleSaveAll}
            type="button"
          />
        )}
      </div>

      {formatId == null ? (
        <div className="surface-card p-6 border-round shadow-1 text-center text-600">
          No format selected. Open this from the Formats View page.
        </div>
      ) : previewLoading ? (
        <div className="snip-page-canvas">
          <Skeleton width="18rem" height="1.75rem" className="mb-2" />
          <Skeleton width="26rem" height="1rem" className="mb-4" />
          {Array.from({ length: 2 }).map((_, i) => (
            <div key={i} className="surface-card border-round shadow-1 p-3 mb-3">
              <Skeleton width="12rem" height="1.25rem" className="mb-3" />
              <Skeleton height="6rem" className="mb-2" />
              <Skeleton width="8rem" height="2rem" />
            </div>
          ))}
        </div>
      ) : !preview ? (
        <div className="surface-card p-6 border-round shadow-1 text-center text-600">
          Could not load this format.
        </div>
      ) : (
        <div className="snip-page-canvas">
          {/* Checklist header — same as Create Request */}
          <ChecklistHeader
            unitName={preview.unit_name}
            formatName={preview.format_name}
            formatNo={preview.format_no}
          />

          {/* Declaration-question status for this format */}
          <div className="flex align-items-center gap-2 mt-2">
            <span className="text-xs text-600">Declaration Questions:</span>
            <Tag
              value={preview.has_declaration_question ? 'Enabled' : 'Disabled'}
              severity={preview.has_declaration_question ? 'success' : 'secondary'}
            />
            {preview.has_declaration_question && (
              <span className="text-500 text-xs">— mark rows as declaration in row settings (non-Basic-Details stages)</span>
            )}
          </div>

          {/* Design surface */}
          <div className="mt-3">
            {loadingConfig && (
              <div className="mb-3">
                <Skeleton height="2.5rem" className="mb-2" />
                <Skeleton height="2.5rem" width="90%" />
              </div>
            )}
            {stages.map((s, i) => (
              <StageConfig
                key={s.key}
                index={i}
                stage={s}
                stageOptions={stageOptions}
                questionChoices={questionChoices}
                ctx={ctx}
                onChange={(next) => updateStage(s.key, next)}
                onRemove={() => removeStage(s.key)}
                onRowDeleted={markRowDeleted}
                onSectionDeleted={markSectionDeleted}
                onToggleHasSection={toggleHasSection}
              />
            ))}

            <Button
              icon="pi pi-sitemap"
              rounded raised
              onClick={addStage}
              type="button"
              className="mt-3 mb-3 snip-add-btn snip-add-btn--stage"
              aria-label="Add Stage"
              tooltip="Add Stage"
              tooltipOptions={{ position: 'top' }}
            />
          </div>
        </div>
      )}
    </div>
  );
};
