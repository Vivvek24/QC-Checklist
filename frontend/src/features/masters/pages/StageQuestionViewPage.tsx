/**
 * Stage Question View Page.
 * Shows format name, lists stages with their mapped questions in a grid below each.
 * Route: /masters/formats-view/:formatId/questions
 */

import { useCallback, useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { Button } from 'primereact/button';
import { Dialog } from 'primereact/dialog';
import { InputSwitch } from 'primereact/inputswitch';
import { InputText } from 'primereact/inputtext';
import { apiClient } from '@shared/services/apiClient';
import { useStages } from '../hooks/useStages';
import { useQuestions } from '../hooks/useQuestions';
import { MasterRowActions } from '../components/MasterRowActions';
import { StageQuestionGrid } from '../components/view/StageQuestionGrid';
import { SectionStageQuestionGrid } from '../components/view/SectionStageQuestionGrid';
import { StageQuestionMappingPage } from './StageQuestionMappingPage';
import { SectionStageQuestionMappingPage } from './SectionStageQuestionMappingPage';
import { AddSectionPage } from './AddSectionPage';
import { BASIC_DETAILS_STAGE } from '../constants';

interface FormatStageMapping {
  id: number;
  format_id: number;
  stage_id: number;
  is_active: boolean;
  has_section: boolean;
}

interface StageQuestionMapping {
  id: number;
  format_stage_mapping_id: number;
  question_id: number;
  section_id: number | null;
  serial_number: number;
  show_on_grid: boolean;
  aql_limit: string;
  is_declaration_question: boolean;
  is_editable: boolean;
  is_active: boolean;
}

interface SectionItem {
  id: number;
  section_name: string;
  format_stage_mapping_id: number | null;
  is_active: boolean;
}

interface FormatDetail {
  format_name: string;
  format_type: string;
  has_declaration_question: boolean;
}

export const StageQuestionViewPage = () => {
  const { formatId } = useParams<{ formatId: string }>();
  const navigate = useNavigate();
  const { data: stagesData } = useStages();
  const { data: questionsData, isLoading: questionsLoading } = useQuestions();
  const stageMap = Object.fromEntries((stagesData?.items ?? []).map((s) => [Number(s.id), s.stage_name]));
  const questionMap = Object.fromEntries((questionsData?.items ?? []).map((q) => [Number(q.id), q.title]));
  const subQuestionIdsMap: Record<number, number[]> = Object.fromEntries(
    (questionsData?.items ?? []).filter((q: any) => q.has_sub_question && q.sub_question_ids?.length)
      .map((q: any) => [Number(q.id), q.sub_question_ids as number[]])
  );

  const [formatDetail, setFormatDetail] = useState<FormatDetail | null>(null);
  const [mappings, setMappings] = useState<FormatStageMapping[]>([]);
  const [questionMappings, setQuestionMappings] = useState<Record<number, StageQuestionMapping[]>>({});
  const [loading, setLoading] = useState(true);

  // Add question popup state
  const [addFormVisible, setAddFormVisible] = useState(false);
  const [selectedMapping, setSelectedMapping] = useState<FormatStageMapping | null>(null);
  const [editingRow, setEditingRow] = useState<StageQuestionMapping | null>(null);

  // Add section popup state
  const [addSectionVisible, setAddSectionVisible] = useState(false);
  const [sectionMapping, setSectionMapping] = useState<FormatStageMapping | null>(null);
  const [sectionsByMapping, setSectionsByMapping] = useState<Record<number, SectionItem[]>>({});

  // Add question to section state
  const [sectionQuestionVisible, setSectionQuestionVisible] = useState(false);
  const [selectedSectionId, setSelectedSectionId] = useState<number | null>(null);

  // Edit section state
  const [editSectionVisible, setEditSectionVisible] = useState(false);
  const [editingSectionId, setEditingSectionId] = useState<number | null>(null);
  const [editingSectionName, setEditingSectionName] = useState('');

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      // Single API call — returns format + all stages + questions + sections in one shot
      const [fmtRes, previewRes] = await Promise.all([
        apiClient.get<FormatDetail & { format_name: string }>(`/masters/formats/${formatId}`),
        apiClient.get<{
          format_id: number; format_name: string; format_no: string;
          stages: Array<{
            format_stage_mapping_id: number; stage_id: number; stage_name: string;
            is_approvable: boolean; has_section: boolean; status: string;
            questions: Array<{ stage_question_mapping_id: number; question_id: number; question_title: string; serial_number: number; section_id: number | null; section_name: string | null }>;
            sections: Array<{ section_id: number; section_name: string; questions: Array<{ stage_question_mapping_id: number; question_id: number; question_title: string; serial_number: number }> }>;
            approval_labels: Array<{ approval_label_id: number; label: string }>;
          }>;
        }>('/qc-checklist/preview', { params: { format_id: formatId } }),
      ]);

      setFormatDetail({ format_name: fmtRes.data.format_name, format_type: fmtRes.data.format_type, has_declaration_question: fmtRes.data.has_declaration_question });

      // Map preview data to existing state shape
      const fsMappings: FormatStageMapping[] = previewRes.data.stages.map((s) => ({
        id: s.format_stage_mapping_id,
        format_id: Number(formatId),
        stage_id: s.stage_id,
        is_active: true,
        has_section: s.has_section,
      }));
      setMappings(fsMappings);

      // Build question mappings from preview (already has question titles resolved)
      const qmMap: Record<number, StageQuestionMapping[]> = {};
      for (const s of previewRes.data.stages) {
        const allQs: StageQuestionMapping[] = [
          ...s.questions.map((q: any) => ({ id: q.stage_question_mapping_id, format_stage_mapping_id: s.format_stage_mapping_id, question_id: q.question_id, section_id: q.section_id, serial_number: q.serial_number, show_on_grid: q.show_on_grid ?? false, aql_limit: q.aql_limit ?? '', is_declaration_question: q.is_declaration_question ?? false, is_editable: q.is_editable ?? true, is_active: true })),
          ...s.sections.flatMap((sec: any) => sec.questions.map((q: any) => ({ id: q.stage_question_mapping_id, format_stage_mapping_id: s.format_stage_mapping_id, question_id: q.question_id, section_id: sec.section_id, serial_number: q.serial_number, show_on_grid: q.show_on_grid ?? false, aql_limit: q.aql_limit ?? '', is_declaration_question: q.is_declaration_question ?? false, is_editable: q.is_editable ?? true, is_active: true }))),
        ];
        qmMap[s.format_stage_mapping_id] = allQs;
      }
      setQuestionMappings(qmMap);

      // Build sections from preview
      const secMap: Record<number, SectionItem[]> = {};
      for (const s of previewRes.data.stages) {
        if (s.has_section && s.sections.length > 0) {
          secMap[s.format_stage_mapping_id] = s.sections.map((sec) => ({
            id: sec.section_id,
            section_name: sec.section_name,
            format_stage_mapping_id: s.format_stage_mapping_id,
            is_active: true,
          }));
        }
      }
      setSectionsByMapping(secMap);
    } catch {
      setFormatDetail(null);
      setMappings([]);
      setQuestionMappings({});
      setSectionsByMapping({});
    } finally { setLoading(false); }
  }, [formatId]);

  useEffect(() => { loadData(); }, [loadData]);

  const openAddQuestion = (mapping: FormatStageMapping) => {
    setSelectedMapping(mapping);
    setAddFormVisible(true);
  };

  // Calculate next serial number for the selected mapping
  const nextSerialNumber = selectedMapping
    ? Math.max(0, ...(questionMappings[selectedMapping.id] ?? []).map((q) => q.serial_number)) + 1
    : 1;

  const deleteQuestionMapping = async (id: number) => {
    try {
      await apiClient.delete(`/masters/stage-question-mappings/${id}`);
      loadData();
    } catch { /* ignore */ }
  };

  const deleteSection = async (id: number) => {
    try {
      await apiClient.delete(`/masters/sections/${id}`);
      loadData();
    } catch { /* ignore */ }
  };

  const editSection = async () => {
    if (!editingSectionId) return;
    try {
      await apiClient.patch(`/masters/sections/${editingSectionId}`, { section_name: editingSectionName });
      setEditSectionVisible(false);
      setEditingSectionId(null);
      loadData();
    } catch { /* ignore */ }
  };

  const toggleHasSection = async (mapping: FormatStageMapping, value: boolean) => {
    try {
      await apiClient.patch(`/masters/format-stage-mappings/${mapping.id}`, { has_section: value });
      setMappings((prev) => prev.map((m) => m.id === mapping.id ? { ...m, has_section: value } : m));
    } catch { /* ignore */ }
  };

  const selectedStageName = selectedMapping ? (stageMap[selectedMapping.stage_id] ?? '') : '';

  return (
    <div className="p-3">
      <div className="flex align-items-center gap-2 mb-3">
        <Button icon="pi pi-arrow-left" severity="secondary" text
          onClick={() => navigate('/masters/formats-view')} type="button" />
        <div>
          <h2 className="text-xl font-semibold text-900 m-0">{formatDetail?.format_name || 'Loading...'}</h2>
          <p className="text-600 mt-1 mb-0">Questions mapped to stages</p>
        </div>
      </div>

      <div className="surface-card p-3 border-round shadow-1">
        {loading || questionsLoading ? (
          <div className="flex align-items-center justify-content-center p-4">
            <i className="pi pi-spin pi-spinner text-2xl" />
          </div>
        ) : mappings.length === 0 ? (
          <p className="text-600">No stages mapped to this format. Add stages first.</p>
        ) : (
          <div className="flex flex-column gap-4">
            {mappings.map((m) => (
              <div key={m.id}>
                {/* Stage header with Add Question button */}
                <div className="flex align-items-center justify-content-between px-2 py-1 border-round mb-2"
                  style={{ background: 'var(--color-surface-ground)', border: '1px solid var(--color-surface-border)' }}>
                  <span className="font-medium" style={{ fontSize: '0.813rem' }}>{stageMap[m.stage_id] ?? `Stage ${m.stage_id}`}</span>
                  <div className="flex align-items-center gap-3">
                    {stageMap[m.stage_id] !== BASIC_DETAILS_STAGE && (
                      <div className="flex align-items-center gap-2">
                        <InputSwitch checked={m.has_section}
                          onChange={(e) => toggleHasSection(m, e.value ?? false)} />
                        <span style={{ fontSize: '0.75rem', color: 'var(--color-text-secondary)' }}>Has Section</span>
                      </div>
                    )}
                    {m.has_section ? (
                      <Button type="button" label="Add Section" icon="pi pi-plus" size="small" outlined
                        onClick={() => { setSectionMapping(m); setAddSectionVisible(true); }} />
                    ) : (
                      <Button type="button" label="Add Question" icon="pi pi-plus" size="small" outlined
                        onClick={() => openAddQuestion(m)} />
                    )}
                  </div>
                </div>

                {/* Questions grid for this stage — hidden when has_section is ON */}
                {!m.has_section && (questionMappings[m.id] ?? []).length > 0 && (
                  <StageQuestionGrid
                    questions={(questionMappings[m.id] ?? []) as any}
                    questionMap={questionMap}
                    onEdit={(row) => { setSelectedMapping(m); setEditingRow(row as any); setAddFormVisible(true); }}
                    onDelete={(id) => deleteQuestionMapping(id)}
                  />
                )}

                {/* Sections grid for this stage (when has_section is ON) */}
                {m.has_section && (sectionsByMapping[m.id] ?? []).length > 0 && (
                  <div style={{ marginLeft: '1rem', marginTop: '0.5rem' }} className="flex flex-column gap-2">
                    {(sectionsByMapping[m.id] ?? []).map((sec) => {
                      const sectionQuestions = (questionMappings[m.id] ?? []).filter((q) => q.section_id === sec.id)
                        .sort((a, b) => a.serial_number - b.serial_number);
                      return (
                        <div key={sec.id}>
                          {/* Section row */}
                          <div className="flex align-items-center justify-content-between px-2 py-1 border-round"
                            style={{ background: '#f0f4f8', border: '1px solid var(--color-surface-border)' }}>
                            <span className="font-medium" style={{ fontSize: '0.78rem' }}>{sec.section_name}</span>
                            <div className="flex align-items-center gap-2">
                              <Button type="button" label="Add Question" icon="pi pi-plus" size="small" text
                                onClick={() => { setSelectedMapping(m); setSelectedSectionId(sec.id); setSectionQuestionVisible(true); }} />
                              <MasterRowActions label={sec.section_name} canUpdate={true} canDelete={true}
                                onEdit={() => { setEditingSectionId(sec.id); setEditingSectionName(sec.section_name); setEditSectionVisible(true); }}
                                onDelete={() => deleteSection(sec.id)} />
                            </div>
                          </div>
                          {/* Questions under this section */}
                          {sectionQuestions.length > 0 && (
                            <SectionStageQuestionGrid
                              questions={sectionQuestions as any}
                              questionMap={questionMap}
                              subQuestionIdsMap={subQuestionIdsMap}
                              onEdit={(row) => { setSelectedMapping(m); setEditingRow(row as any); setSelectedSectionId(sec.id); setSectionQuestionVisible(true); }}
                              onDelete={(id) => deleteQuestionMapping(id)}
                            />
                          )}
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Add Question popup — from StageQuestionMappingPage */}
      {formatDetail && selectedMapping && (
        <StageQuestionMappingPage
          visible={addFormVisible}
          formatStageMappingId={selectedMapping.id}
          stageName={selectedStageName}
          formatType={formatDetail.format_type}
          hasDeclarationQuestion={formatDetail.has_declaration_question}
          defaultSerialNumber={nextSerialNumber}
          initialData={editingRow ? {
            serial_number: editingRow.serial_number,
            question_id: editingRow.question_id,
            show_on_grid: editingRow.show_on_grid,
            aql_limit: editingRow.aql_limit || '',
            is_editable: editingRow.is_editable,
            is_declaration_question: editingRow.is_declaration_question,
            is_active: editingRow.is_active,
          } : undefined}
          editingId={editingRow?.id ?? null}
          onHide={() => { setAddFormVisible(false); setSelectedMapping(null); setEditingRow(null); }}
          onSuccess={loadData}
        />
      )}

      {/* Add Section popup */}
      {sectionMapping && (
        <AddSectionPage
          visible={addSectionVisible}
          formatStageMappingId={sectionMapping.id}
          onHide={() => { setAddSectionVisible(false); setSectionMapping(null); }}
          onSuccess={loadData}
        />
      )}

      {/* Add Question to Section popup */}
      {formatDetail && selectedMapping && sectionQuestionVisible && selectedSectionId && (
        <SectionStageQuestionMappingPage
          visible={sectionQuestionVisible}
          formatStageMappingId={selectedMapping.id}
          sectionId={selectedSectionId}
          formatType={formatDetail.format_type}
          hasDeclarationQuestion={formatDetail.has_declaration_question}
          defaultSerialNumber={nextSerialNumber}
          editingId={editingRow?.id ?? null}
          initialData={editingRow ? {
            serial_number: editingRow.serial_number,
            question_id: editingRow.question_id,
            aql_limit: editingRow.aql_limit || '',
            is_declaration_question: editingRow.is_declaration_question,
            is_active: editingRow.is_active,
          } : undefined}
          onHide={() => { setSectionQuestionVisible(false); setSelectedSectionId(null); setSelectedMapping(null); setEditingRow(null); }}
          onSuccess={loadData}
        />
      )}

      {/* Edit Section dialog */}
      {editSectionVisible && (
        <Dialog header="Edit Section" visible={editSectionVisible}
          onHide={() => setEditSectionVisible(false)} style={{ width: '380px' }} modal
          footer={
            <div className="flex justify-content-end gap-2">
              <Button label="Cancel" severity="secondary" outlined onClick={() => setEditSectionVisible(false)} type="button" />
              <Button label="Save" onClick={editSection} type="button" />
            </div>
          }
        >
          <div className="flex flex-column gap-2 pt-2">
            <label className="font-medium text-sm">Section Name</label>
            <InputText value={editingSectionName} onChange={(e) => setEditingSectionName(e.target.value)} />
          </div>
        </Dialog>
      )}
    </div>
  );
};
