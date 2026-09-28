/**
 * Template API — persists the checklist column layout for a format's stages
 * and sections. Backed by backend/src/api/v1/endpoints/template_controller.py.
 *
 * The backend stores columns flat (each column row carries its own
 * format_stage_mapping_id/section_id scope) under a `templates` anchor row
 * per format. This client groups flat columns by scope for the page's needs.
 */

import { apiClient } from '@shared/services/apiClient';

export interface TemplateColumnInput {
  header: string;
  column_type: string;
  width?: string | null;
  is_required?: boolean;
}

export interface TemplateColumnResponse {
  id: number;
  template_id: number;
  format_stage_mapping_id: number;
  section_id: number | null;
  header: string;
  column_type: string;
  display_order: number;
  width: string | null;
  is_required: boolean;
}

export interface TemplateResponse {
  id: number;
  format_id: number;
  is_active: boolean;
  created_by: string;
  created_date: string;
  modified_by: string;
  modified_date: string;
}

/** A single stage_question_mappings row within a bulk stage save. */
export interface StageSaveRowInput {
  question_id: number;
  mapping_id?: number | null;
  show_on_grid?: boolean;
  sap_field_id?: number | null;
  is_editable?: boolean;
  is_declaration_question?: boolean;
  custom_answers?: string | null;
  aql_limit?: string;
  is_active?: boolean;
}

/** A single section (and its own rows/columns) within a bulk stage save. */
export interface StageSaveSectionInput {
  section_name: string;
  section_id?: number | null;
  rows: StageSaveRowInput[];
  columns: TemplateColumnInput[];
}

export interface TemplateStageSaveRequest {
  format_id: number;
  stage_id: number;
  rows: StageSaveRowInput[];
  columns: TemplateColumnInput[];
  sections: StageSaveSectionInput[];
  deleted_mapping_ids: number[];
  deleted_section_ids: number[];
}

export interface StageSaveRowResult {
  id: number;
  question_id: number;
  serial_number: number;
}

export interface StageSaveSectionResult {
  id: number;
  section_name: string;
  rows: StageSaveRowResult[];
}

export interface TemplateStageSaveResponse {
  format_stage_mapping_id: number;
  rows: StageSaveRowResult[];
  sections: StageSaveSectionResult[];
}

export const templateApi = {
  /** Get (or lazily create) the template anchor for a format. */
  getOrCreateForFormat: async (formatId: number): Promise<TemplateResponse> => {
    const { data } = await apiClient.get<TemplateResponse>(`/templates/by-format/${formatId}`);
    return data;
  },

  /** Columns for a single scope: a stage (section_id null) or a section. */
  getColumnsForScope: async (
    formatStageMappingId: number,
    sectionId: number | null
  ): Promise<TemplateColumnResponse[]> => {
    const { data } = await apiClient.get<{ items: TemplateColumnResponse[] }>('/templates/columns', {
      params: { format_stage_mapping_id: formatStageMappingId, section_id: sectionId ?? undefined },
    });
    return data.items;
  },

  /** All columns (stage-level and every section) under one stage mapping. */
  listColumnsForStage: async (formatStageMappingId: number): Promise<TemplateColumnResponse[]> => {
    const { data } = await apiClient.get<{ items: TemplateColumnResponse[] }>('/templates/columns/by-stage', {
      params: { format_stage_mapping_id: formatStageMappingId },
    });
    return data.items;
  },

  /** Replace all columns for a stage/section scope, in order. */
  replaceColumnsForScope: async (
    formatId: number,
    formatStageMappingId: number,
    sectionId: number | null,
    columns: TemplateColumnInput[]
  ): Promise<TemplateColumnResponse[]> => {
    const { data } = await apiClient.put<{ items: TemplateColumnResponse[] }>('/templates/columns', {
      format_id: formatId,
      format_stage_mapping_id: formatStageMappingId,
      section_id: sectionId,
      columns,
    });
    return data.items;
  },

  /**
   * Atomically save an entire stage — its own rows/columns, every nested
   * section's rows/columns, and any rows/sections removed since the last
   * save — in one request/DB transaction. Replaces the old approach of many
   * sequential create/update/delete calls per row/section/scope.
   *
   * Keyed by `stage_id` (from the Stage master) rather than an existing
   * format_stage_mapping id — the stage picker lists every stage, so a
   * freshly-picked stage may have no mapping yet. The backend resolves (or
   * creates) the mapping and returns its id in the response.
   */
  saveStage: async (request: TemplateStageSaveRequest): Promise<TemplateStageSaveResponse> => {
    const { data } = await apiClient.put<TemplateStageSaveResponse>('/templates/stages/save', request);
    return data;
  },
};
