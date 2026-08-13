/**
 * Add Section Page — popup component that creates a section via the Section API.
 * Called from StageQuestionViewPage when has_section is ON.
 */

import { useRef, useState } from 'react';
import { Toast } from 'primereact/toast';
import { apiClient } from '@shared/services/apiClient';
import { AddSectionForm } from '../components/AddSectionForm';

interface Props {
  visible: boolean;
  onHide: () => void;
  onSuccess: () => void;
  formatStageMappingId: number;
}

export const AddSectionPage = ({ visible, onHide, onSuccess, formatStageMappingId }: Props) => {
  const toast = useRef<Toast>(null);
  const [saving, setSaving] = useState(false);

  const handleSubmit = async (data: { section_name: string }) => {
    setSaving(true);
    try {
      await apiClient.post('/masters/sections', {
        section_name: data.section_name,
        format_stage_mapping_id: formatStageMappingId,
        is_active: true,
      });
      toast.current?.show({ severity: 'success', summary: 'Section created', life: 3000 });
      onSuccess();
      onHide();
    } catch (e: any) {
      toast.current?.show({ severity: 'error', summary: 'Error', detail: e?.response?.data?.detail || 'Failed', life: 5000 });
    } finally { setSaving(false); }
  };

  return (
    <>
      <Toast ref={toast} />
      <AddSectionForm visible={visible} saving={saving} onHide={onHide} onSubmit={handleSubmit} />
    </>
  );
};
