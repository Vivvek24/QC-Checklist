/**
 * useTemplateConfigData — hydrates the design canvas (stages, sections, rows,
 * columns) for a format's checklist preview.
 *
 * Everything it needs is already on the single preview response: each stage's
 * (and section's) rows (questions) and saved column layout. It builds
 * DesignStage[] from that in one pass — no extra per-stage API calls. Only
 * stages that already have some saved data (rows and/or columns) are added to
 * the canvas; an empty stage is something the user adds explicitly via
 * "Add Stage".
 */

import { useEffect, useState } from 'react';
import type {
  ChecklistPreview,
  ChecklistStagePreview,
  ColumnPreview,
  QuestionAnswerPreview,
  SectionPreview,
} from '../models/Preview';
import type { DesignStage, DesignSection, DesignRow, DesignColumn, ColumnRender } from '../models/DesignSpec';
import { emptyStage, emptySection, newColumnKey, newRowKey } from '../models/DesignSpec';

/** Build a DesignRow from a preview question (its row-level attributes). */
const toDesignRow = (q: QuestionAnswerPreview): DesignRow => ({
  key: newRowKey(),
  mappingId: q.stage_question_mapping_id,
  questionId: q.question_id,
  showOnGrid: q.show_on_grid,
  sapFieldId: q.sap_field_id,
  isEditable: q.is_editable,
  isDeclaration: q.is_declaration_question,
  customAnswer: q.custom_answers,
  aqlLimit: q.aql_limit,
});

/** Build DesignColumns from a list of columns for one scope. */
const toDesignColumns = (cols: ColumnPreview[]): DesignColumn[] =>
  cols
    .slice()
    .sort((a, b) => a.display_order - b.display_order)
    .map((c) => ({
      key: newColumnKey(),
      header: c.header,
      render: c.column_type as ColumnRender,
      width: c.width ?? undefined,
    }));

/** Build a DesignSection from a preview section. */
const toDesignSection = (sec: SectionPreview): DesignSection => ({
  ...emptySection(),
  sectionId: sec.section_id,
  sectionName: sec.section_name,
  rows: sec.questions.map(toDesignRow),
  columns: toDesignColumns(sec.columns),
});

/** Build a DesignStage from a preview stage, or null if it has no saved data. */
const toDesignStage = (stage: ChecklistStagePreview): DesignStage | null => {
  const stageRows = stage.questions.map(toDesignRow);
  // Only sections that actually have rows and/or saved columns.
  const sections = stage.sections
    .filter((s) => s.questions.length > 0 || s.columns.length > 0)
    .map(toDesignSection);

  const hasAnyData = stageRows.length > 0 || stage.columns.length > 0 || sections.length > 0;
  if (!hasAnyData) return null;

  return {
    ...emptyStage(),
    stageFsmId: stage.format_stage_mapping_id,
    stageId: stage.stage_id,
    stageName: stage.stage_name,
    rows: stageRows,
    columns: toDesignColumns(stage.columns),
    sections,
    hasSection: stage.has_section,
  };
};

export interface UseTemplateConfigDataResult {
  stages: DesignStage[];
  setStages: React.Dispatch<React.SetStateAction<DesignStage[]>>;
  loadingConfig: boolean;
}

export const useTemplateConfigData = (
  preview: ChecklistPreview | undefined
): UseTemplateConfigDataResult => {
  const [stages, setStages] = useState<DesignStage[]>([]);
  // Kept for API compatibility with the page; hydration is now synchronous
  // off the preview, so this is only ever briefly true, if at all.
  const [loadingConfig, setLoadingConfig] = useState(false);

  useEffect(() => {
    if (!preview) {
      setStages([]);
      return;
    }
    setLoadingConfig(true);
    const built = preview.stages
      .map(toDesignStage)
      .filter((s): s is DesignStage => s !== null);
    setStages(built);
    setLoadingConfig(false);
  }, [preview]);

  return { stages, setStages, loadingConfig };
};
