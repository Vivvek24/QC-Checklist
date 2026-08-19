/**
 * Section Stage Question Mapping Page — popup for adding/editing a question mapping under a section.
 * Called from StageQuestionViewPage when has_section is ON.
 */

import { useRef, useState } from 'react';
import { Toast } from 'primereact/toast';
import { apiClient } from '@shared/services/apiClient';
import { AddSectionStageQuestionForm, type SectionStageQuestionFormData } from '../components/AddSectionStageQuestionForm';

interface Props {
  visible: boolean;
  formatStageMappingId: number;
  sectionId: number;
  formatType: string;
  hasDeclarationQuestion: boolean;
  defaultSerialNumber?: number;
  initialData?: Partial<SectionStageQuestionFormData>;
  editingId?: number | null;
  onHide: () => void;
  onSuccess: () => void;
}

export const SectionStageQuestionMappingPage = ({ visible, formatStageMappingId, sectionId, formatType, hasDeclarationQuestion, defaultSerialNumber, initialData, editingId, onHide, onSuccess }: Props) => {
  const toast = useRef<Toast>(null);
  const [saving, setSaving] = useState(false);

  const handleSubmit = async (data: SectionStageQuestionFormData) => {
    setSaving(true);
    try {
      if (editingId) {
        // PATCH — update existing
        await apiClient.patch(`/masters/stage-question-mappings/${editingId}`, {
          question_id: data.question_id,
          serial_number: data.serial_number,
          aql_limit: data.aql_limit,
          is_declaration_question: data.is_declaration_question,
          is_active: data.is_active,
        });
        toast.current?.show({ severity: 'success', summary: 'Question mapping updated', life: 3000 });
      } else {
        // POST — create new
        await apiClient.post('/masters/stage-question-mappings', {
          format_stage_mapping_id: formatStageMappingId,
          question_id: data.question_id,
          serial_number: data.serial_number,
          section_id: sectionId,
          aql_limit: data.aql_limit,
          is_declaration_question: data.is_declaration_question,
          show_on_grid: false,
          is_editable: true,
          is_active: data.is_active,
        });
        toast.current?.show({ severity: 'success', summary: 'Question mapping created', life: 3000 });
      }
      onSuccess();
      onHide();
    } catch (e: any) {
      toast.current?.show({ severity: 'error', summary: 'Error', detail: e?.response?.data?.detail || 'Failed', life: 5000 });
    } finally { setSaving(false); }
  };

  return (
    <>
      <Toast ref={toast} />
      <AddSectionStageQuestionForm
        visible={visible}
        formatType={formatType}
        hasDeclarationQuestion={hasDeclarationQuestion}
        defaultSerialNumber={defaultSerialNumber}
        initialData={initialData}
        saving={saving}
        onHide={onHide}
        onSubmit={handleSubmit}
      />
    </>
  );
};
