/**
 * Stage Question Mapping Page — popup dialog for adding a question mapping.
 * This page component renders as a Dialog and is called from StageQuestionViewPage.
 * It receives context (stageName, formatType, etc.) as props.
 */

import { useRef, useState } from 'react';
import { Toast } from 'primereact/toast';
import { apiClient } from '@shared/services/apiClient';
import { AddStageQuestionForm, type AddStageQuestionFormData } from '../components/AddStageQuestionForm';

interface Props {
  visible: boolean;
  formatStageMappingId: number;
  stageName: string;
  formatType: string;
  hasDeclarationQuestion: boolean;
  defaultSerialNumber?: number;
  initialData?: Partial<AddStageQuestionFormData>;
  editingId?: number | null;
  sectionId?: number | null;
  onHide: () => void;
  onSuccess: () => void;
}

export const StageQuestionMappingPage = ({ visible, formatStageMappingId, stageName, formatType, hasDeclarationQuestion, defaultSerialNumber, initialData, editingId, sectionId, onHide, onSuccess }: Props) => {
  const toast = useRef<Toast>(null);
  const [saving, setSaving] = useState(false);

  const handleSubmit = async (data: AddStageQuestionFormData) => {
    setSaving(true);
    try {
      if (editingId) {
        await apiClient.patch(`/masters/stage-question-mappings/${editingId}`, {
          question_id: data.question_id,
          serial_number: data.serial_number,
          show_on_grid: data.show_on_grid,
          sap_field_id: data.sap_field_id,
          is_editable: data.is_editable,
          is_declaration_question: data.is_declaration_question,
          custom_answers: data.custom_answers,
          aql_limit: data.aql_limit,
          is_active: data.is_active,
        });
        toast.current?.show({ severity: 'success', summary: 'Question mapping updated', life: 3000 });
      } else {
        await apiClient.post('/masters/stage-question-mappings', {
          format_stage_mapping_id: formatStageMappingId,
          question_id: data.question_id,
          serial_number: data.serial_number,
          show_on_grid: data.show_on_grid,
          sap_field_id: data.sap_field_id,
          section_id: sectionId ?? null,
          is_editable: data.is_editable,
          is_declaration_question: data.is_declaration_question,
          custom_answers: data.custom_answers,
          aql_limit: data.aql_limit,
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
      <AddStageQuestionForm
        visible={visible}
        stageName={stageName}
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
