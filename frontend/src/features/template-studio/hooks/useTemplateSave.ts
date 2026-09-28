/**
 * useTemplateSave — persists the design canvas.
 *
 * Each stage is saved in a single atomic request (PUT
 * /templates/stages/save, keyed by stage_id): its own rows (stage_question_mappings) +
 * columns (template_layout_columns), every nested section's rows + columns,
 * and any rows/sections removed from the canvas since the last save — all in
 * one DB transaction on the backend, so a stage's save is all-or-nothing.
 *
 * Tracks rows/sections removed from the canvas since the last save (their
 * backing DB records are deleted when Save runs, so removal is never lost).
 * Pending deletions aren't tied to any particular stage any more (the row/
 * section they belonged to is gone from the canvas) — they just need to be
 * sent exactly once across the whole Save Configuration run, so they're all
 * attached to the first stage's save call and cleared immediately after.
 */

import { useRef, useState } from 'react';
import type { DesignStage, DesignSection, DesignRow } from '../models/DesignSpec';
import { templateApi, type StageSaveRowInput, type StageSaveSectionInput } from '../api/templateApi';

export interface UseTemplateSaveOptions {
  stages: DesignStage[];
  setStages: (stages: DesignStage[]) => void;
  formatId: number | null;
  onSuccess?: () => void;
  onError?: (detail: string) => void;
}

export interface UseTemplateSaveResult {
  saving: boolean;
  handleSaveAll: () => Promise<void>;
  markRowDeleted: (mappingId: number) => void;
  markSectionDeleted: (section: DesignSection) => void;
  markStageRemoved: (stageId: number | null) => void;
}

/** Build the row payload the backend expects for one row. */
const toRowInput = (row: DesignRow): StageSaveRowInput => ({
  question_id: row.questionId!,
  mapping_id: row.mappingId ?? null,
  show_on_grid: row.showOnGrid ?? false,
  sap_field_id: row.sapFieldId ?? null,
  is_editable: row.isEditable ?? true,
  is_declaration_question: row.isDeclaration ?? false,
  custom_answers: row.customAnswer ?? null,
  aql_limit: row.aqlLimit ?? '',
  // Template Studio has no per-row Active toggle — rows it manages are
  // always active. (The field is still stored/filterable via the standalone
  // masters endpoints; nothing in the checklist render/fill-in path reads it.)
  is_active: true,
});

export const useTemplateSave = ({
  stages,
  setStages,
  formatId,
  onSuccess,
  onError,
}: UseTemplateSaveOptions): UseTemplateSaveResult => {
  const [saving, setSaving] = useState(false);
  const pendingRowDeletions = useRef<Set<number>>(new Set());
  const pendingSectionDeletions = useRef<DesignSection[]>([]);

  // A deletion's own stage/section id doesn't matter to the backend (it
  // deletes by raw mapping/section id, regardless of which stage the save
  // call is for) — but *some* valid stage_id is still needed to call the
  // save endpoint at all. Remember the last stage a deletion came from so
  // there's still a stage to call even if the user goes on to delete every
  // stage from the canvas.
  const lastKnownStageId = useRef<number | null>(null);

  const markRowDeleted = (mappingId: number) => {
    pendingRowDeletions.current.add(mappingId);
  };
  const markSectionDeleted = (section: DesignSection) => {
    pendingSectionDeletions.current.push(section);
  };
  const markStageRemoved = (stageId: number | null) => {
    if (stageId != null) lastKnownStageId.current = stageId;
  };

  /**
   * Rows with no question picked, or a question picked on more than one row
   * within the same scope (a stage's own rows, or one section's rows — each
   * scope is checked independently, matching the original form's per-scope
   * uniqueness rule). ConfigTable highlights these same rows inline; this is
   * the pre-flight gate that actually blocks Save. The backend re-checks
   * this too (it owns the real duplicate rule, scoped per stage rather than
   * per section — see TemplateStageSaveService), so this is a fast local
   * pre-check, not the source of truth.
   */
  const findInvalidScope = (): string | null => {
    const checkRows = (rows: DesignRow[]): boolean => {
      if (rows.some((r) => !r.questionId)) return false;
      const counts = new Map<number, number>();
      for (const r of rows) {
        if (r.questionId) counts.set(r.questionId, (counts.get(r.questionId) ?? 0) + 1);
      }
      return ![...counts.values()].some((n) => n > 1);
    };

    for (const stage of stages) {
      if (!stage.stageId) continue; // no stage picked yet — nothing to save for it
      const stageLabel = stage.stageName || `Stage ${stages.indexOf(stage) + 1}`;
      if (!stage.hasSection && !checkRows(stage.rows)) {
        return `"${stageLabel}" has a row with no question selected, or the same question selected twice.`;
      }
      for (const section of stage.sections) {
        if (!checkRows(section.rows)) {
          const sectionLabel = section.sectionName || 'Untitled Section';
          return `"${stageLabel} → ${sectionLabel}" has a row with no question selected, or the same question selected twice.`;
        }
      }
    }
    return null;
  };

  /**
   * Save one stage — its rows/columns and sections, plus whatever pending
   * deletions are passed in (only the first stage saved in a run carries
   * any, see handleSaveAll), in one atomic call.
   */
  const saveStage = async (
    stage: DesignStage,
    formatIdValue: number,
    deletedMappingIds: number[],
    deletedSectionIds: number[]
  ): Promise<DesignStage> => {
    if (!stage.stageId) return stage; // nothing to persist without a picked stage

    const sections: StageSaveSectionInput[] = stage.sections.map((section) => ({
      section_name: section.sectionName || 'Untitled Section',
      section_id: section.sectionId ?? null,
      rows: section.rows.map(toRowInput),
      columns: section.columns.map((c) => ({
        header: c.header,
        column_type: c.render,
        width: c.width ?? null,
        is_required: c.required ?? false,
      })),
    }));

    const result = await templateApi.saveStage({
      format_id: formatIdValue,
      stage_id: stage.stageId,
      rows: stage.rows.map(toRowInput),
      columns: stage.columns.map((c) => ({
        header: c.header,
        column_type: c.render,
        width: c.width ?? null,
        is_required: c.required ?? false,
      })),
      sections,
      deleted_mapping_ids: deletedMappingIds,
      deleted_section_ids: deletedSectionIds,
    });

    // Fill in mappingId/sectionId for anything that was newly created, using
    // the backend's returned ids in the same order the rows/sections were sent.
    const savedRows: DesignRow[] = stage.rows.map((row, i) => ({
      ...row,
      mappingId: result.rows[i]?.id ?? row.mappingId,
    }));
    const savedSections: DesignSection[] = stage.sections.map((section, i) => {
      const sectionResult = result.sections[i];
      return {
        ...section,
        sectionId: sectionResult?.id ?? section.sectionId,
        rows: section.rows.map((row, j) => ({
          ...row,
          mappingId: sectionResult?.rows[j]?.id ?? row.mappingId,
        })),
      };
    });

    // The backend resolves/creates the format_stage_mapping — remember its
    // id so later saves (has_section PATCH, approval-label lookups by fsm)
    // and the "no stages left" deletion fallback still have a valid fsm_id.
    return {
      ...stage,
      stageFsmId: result.format_stage_mapping_id,
      rows: savedRows,
      sections: savedSections,
    };
  };

  const handleSaveAll = async () => {
    if (formatId == null) return;
    const invalidScope = findInvalidScope();
    if (invalidScope) {
      onError?.(invalidScope);
      return;
    }
    setSaving(true);
    try {
      // Pending deletions are sent exactly once, attached to the first
      // stage's save call — the row/section they belonged to is already
      // gone from the canvas, so which stage's request carries them doesn't
      // matter, only that they go through exactly once.
      const deletedMappingIds = [...pendingRowDeletions.current];
      const deletedSectionIds = pendingSectionDeletions.current
        .map((s) => s.sectionId)
        .filter((id): id is number => id != null);
      const hasPendingDeletions = deletedMappingIds.length > 0 || deletedSectionIds.length > 0;

      const saved: DesignStage[] = [];
      for (let i = 0; i < stages.length; i++) {
        const isFirst = i === 0;
        saved.push(
          await saveStage(
            stages[i]!,
            formatId,
            isFirst ? deletedMappingIds : [],
            isFirst ? deletedSectionIds : []
          )
        );
      }

      // No stages left on the canvas at all, but rows/sections were removed
      // before their stage was deleted — still send those deletions using
      // the last stage we know a valid fsm_id for.
      if (stages.length === 0 && hasPendingDeletions && lastKnownStageId.current != null) {
        await templateApi.saveStage({
          format_id: formatId,
          stage_id: lastKnownStageId.current,
          rows: [],
          columns: [],
          sections: [],
          deleted_mapping_ids: deletedMappingIds,
          deleted_section_ids: deletedSectionIds,
        });
      }

      pendingRowDeletions.current.clear();
      pendingSectionDeletions.current = [];

      setStages(saved);
      onSuccess?.();
    } catch (e) {
      const detail = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      onError?.(detail || 'Please try again.');
    } finally {
      setSaving(false);
    }
  };

  return { saving, handleSaveAll, markRowDeleted, markSectionDeleted, markStageRemoved };
};
