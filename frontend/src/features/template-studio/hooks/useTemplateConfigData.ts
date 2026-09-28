/**
 * useTemplateConfigData — loads and hydrates the design canvas (stages,
 * sections, rows, columns) for a format's checklist preview.
 *
 * On every preview change, for each stage mapped to the format it pulls the
 * saved rows (stage_question_mappings) and the saved column layout
 * (templates), and rebuilds DesignStage[] from them. Only stages that already
 * have some saved data (rows and/or columns) are added to the canvas — an
 * empty stage is something the user adds explicitly via "Add Stage".
 */

import { useEffect, useState } from 'react';
import { apiClient } from '@shared/services/apiClient';
import type { ChecklistPreview } from '../models/Preview';
import type { DesignStage, DesignSection, DesignRow, DesignColumn, ColumnRender } from '../models/DesignSpec';
import { emptyStage, emptySection, newColumnKey, newRowKey } from '../models/DesignSpec';
import { templateApi, type TemplateColumnResponse } from '../api/templateApi';

/** Raw shape returned by GET /masters/stage-question-mappings. */
export interface RawMapping {
  id: number;
  format_stage_mapping_id: number;
  question_id: number;
  section_id: number | null;
  serial_number: number;
  show_on_grid: boolean;
  sap_field_id: number | null;
  is_editable: boolean;
  is_declaration_question: boolean;
  custom_answers: string | null;
  aql_limit: string;
  is_active: boolean;
}

/** Build a DesignRow from a persisted mapping (its row-level attributes). */
const toDesignRow = (m: RawMapping): DesignRow => ({
  key: newRowKey(),
  mappingId: m.id,
  questionId: m.question_id,
  showOnGrid: m.show_on_grid,
  sapFieldId: m.sap_field_id,
  isEditable: m.is_editable,
  isDeclaration: m.is_declaration_question,
  customAnswer: m.custom_answers,
  aqlLimit: m.aql_limit,
});

/** Build DesignColumns from a flat list of columns for one scope. */
const toDesignColumns = (cols: TemplateColumnResponse[]): DesignColumn[] =>
  cols
    .slice()
    .sort((a, b) => a.display_order - b.display_order)
    .map((c) => ({
      key: newColumnKey(),
      header: c.header,
      render: c.column_type as ColumnRender,
      width: c.width ?? undefined,
    }));

export interface UseTemplateConfigDataResult {
  stages: DesignStage[];
  setStages: React.Dispatch<React.SetStateAction<DesignStage[]>>;
  loadingConfig: boolean;
}

export const useTemplateConfigData = (
  preview: ChecklistPreview | undefined
): UseTemplateConfigDataResult => {
  const [stages, setStages] = useState<DesignStage[]>([]);
  const [loadingConfig, setLoadingConfig] = useState(false);

  useEffect(() => {
    if (!preview) {
      setStages([]);
      return;
    }
    let cancelled = false;

    const load = async () => {
      setLoadingConfig(true);
      try {
        const built: DesignStage[] = [];
        for (const stagePreview of preview.stages) {
          const fsmId = stagePreview.format_stage_mapping_id;
          const [mappingsRes, columnsRes] = await Promise.all([
            apiClient.get<{ items: RawMapping[] }>('/masters/stage-question-mappings', {
              params: { format_stage_mapping_id: fsmId },
            }),
            templateApi.listColumnsForStage(fsmId),
          ]);
          const mappings = mappingsRes.data.items;
          const stageColumns = columnsRes.filter((c) => c.section_id == null);
          const stageRows = mappings.filter((m) => m.section_id == null).map(toDesignRow);

          // Build sections that have rows and/or saved columns.
          const sectionIdsWithData = new Set<number>([
            ...mappings.filter((m) => m.section_id != null).map((m) => m.section_id as number),
            ...columnsRes.filter((c) => c.section_id != null).map((c) => c.section_id as number),
          ]);
          const sections: DesignSection[] = Array.from(sectionIdsWithData).map((sectionId) => {
            const sectionPreview = stagePreview.sections.find((s) => s.section_id === sectionId);
            const sectionColumns = columnsRes.filter((c) => c.section_id === sectionId);
            const rows = mappings.filter((m) => m.section_id === sectionId).map(toDesignRow);
            return {
              ...emptySection(),
              sectionId,
              sectionName: sectionPreview?.section_name ?? '',
              rows,
              columns: toDesignColumns(sectionColumns),
            };
          });

          const hasAnyData = stageRows.length > 0 || stageColumns.length > 0 || sections.length > 0;
          if (!hasAnyData) continue;

          built.push({
            ...emptyStage(),
            stageFsmId: fsmId,
            stageId: stagePreview.stage_id,
            stageName: stagePreview.stage_name,
            rows: stageRows,
            columns: toDesignColumns(stageColumns),
            sections,
            hasSection: stagePreview.has_section,
          });
        }
        if (!cancelled) setStages(built);
      } catch {
        if (!cancelled) setStages([]);
      } finally {
        if (!cancelled) setLoadingConfig(false);
      }
    };

    load();
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [preview]);

  return { stages, setStages, loadingConfig };
};
