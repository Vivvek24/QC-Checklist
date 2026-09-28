// Template Studio feature barrel export
export { TemplateConfigPage } from './pages/TemplateConfigPage';

export { StageConfig } from './components/StageConfig';
export type { StageOption, QuestionChoice } from './components/StageConfig';
export { SectionConfig } from './components/SectionConfig';
export { ConfigTable } from './components/ConfigTable';

export { useChecklistPreview } from './hooks/useChecklistPreview';
export { useDragReorder, moveItem } from './hooks/useDragReorder';
export type { UseDragReorderOptions, UseDragReorderResult } from './hooks/useDragReorder';
export { useTemplateConfigData } from './hooks/useTemplateConfigData';
export type { RawMapping, UseTemplateConfigDataResult } from './hooks/useTemplateConfigData';
export { useQuestionChoices } from './hooks/useQuestionChoices';
export type { QuestionMasterRow } from './hooks/useQuestionChoices';
export { useTemplateSave } from './hooks/useTemplateSave';
export type { UseTemplateSaveOptions, UseTemplateSaveResult } from './hooks/useTemplateSave';

export { templateApi } from './api/templateApi';
export type {
  TemplateColumnInput,
  TemplateColumnResponse,
  TemplateResponse,
  StageSaveRowInput,
  StageSaveSectionInput,
  TemplateStageSaveRequest,
  StageSaveRowResult,
  StageSaveSectionResult,
  TemplateStageSaveResponse,
} from './api/templateApi';

export {
  COLUMN_RENDERS,
  columnRenderMeta,
  emptyStage,
  emptySection,
  newStageKey,
  newSectionKey,
  newColumnKey,
  newRowKey,
} from './models/DesignSpec';
export type { DesignSpec, DesignStage, DesignSection, DesignColumn, DesignRow, ColumnRender } from './models/DesignSpec';
export type { ChecklistPreview, ChecklistStagePreview, SectionPreview, QuestionAnswerPreview } from './models/Preview';
