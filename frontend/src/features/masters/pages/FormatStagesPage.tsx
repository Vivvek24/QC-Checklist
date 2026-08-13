/**
 * Format Stages Page — shows stages mapped to a specific format.
 * Route: /masters/stage-question-mapping/:formatId/stages
 */

import { useCallback, useEffect, useRef, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { Button } from 'primereact/button';
import { Column } from 'primereact/column';
import { DataTable } from 'primereact/datatable';
import { Dialog } from 'primereact/dialog';
import { Dropdown } from 'primereact/dropdown';
import { InputSwitch } from 'primereact/inputswitch';
import { Toast } from 'primereact/toast';
import { Controller, useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { apiClient } from '@shared/services/apiClient';
import { useStages } from '../hooks/useStages';
import { MasterRowActions } from '../components/MasterRowActions';

interface FormatStageMapping {
  id: number;
  format_id: number;
  stage_id: number;
  is_active: boolean;
  is_approvable: boolean;
  is_refer_back: boolean;
  has_section: boolean;
}

const addSchema = z.object({
  stage_id: z.number({ required_error: 'Stage is required' }).min(1),
  is_active: z.boolean(),
});
type AddFD = z.infer<typeof addSchema>;

export const FormatStagesPage = () => {
  const { formatId } = useParams<{ formatId: string }>();
  const navigate = useNavigate();
  const toast = useRef<Toast>(null);
  const { data: stagesData } = useStages();

  const stageOptions = (stagesData?.items ?? []).map((s) => ({ label: s.stage_name, value: Number(s.id) }));
  const stageMap = Object.fromEntries((stagesData?.items ?? []).map((s) => [Number(s.id), s.stage_name]));

  const [mappings, setMappings] = useState<FormatStageMapping[]>([]);
  const [loading, setLoading] = useState(true);
  const [formatName, setFormatName] = useState('');
  const [addVisible, setAddVisible] = useState(false);

  const { handleSubmit, control, reset } = useForm<AddFD>({
    resolver: zodResolver(addSchema), defaultValues: { stage_id: 0, is_active: true },
  });

  const loadMappings = useCallback(async () => {
    setLoading(true);
    try {
      const { data } = await apiClient.get<{ items: FormatStageMapping[] }>(
        '/masters/format-stage-mappings', { params: { format_id: formatId } }
      );
      const items = data.items ?? [];

      // Auto-create "Basic Details" stage mapping if it doesn't exist
      const allStages = stagesData?.items ?? [];
      const basicDetailsStage = allStages.find((s) => s.stage_name === 'Basic Details');
      if (basicDetailsStage && !items.some((m) => m.stage_id === Number(basicDetailsStage.id))) {
        try {
          await apiClient.post('/masters/format-stage-mappings', {
            format_id: Number(formatId), stage_id: Number(basicDetailsStage.id), is_active: true,
          });
          // Reload after auto-creation
          const { data: refreshed } = await apiClient.get<{ items: FormatStageMapping[] }>(
            '/masters/format-stage-mappings', { params: { format_id: formatId } }
          );
          setMappings(refreshed.items ?? []);
        } catch { setMappings(items); }
      } else {
        setMappings(items);
      }
    } catch { setMappings([]); }
    finally { setLoading(false); }
  }, [formatId, stagesData]);

  const loadFormatName = useCallback(async () => {
    try {
      const { data } = await apiClient.get<{ format_name: string }>(`/masters/formats/${formatId}`);
      setFormatName(data.format_name);
    } catch { setFormatName(''); }
  }, [formatId]);

  useEffect(() => { loadMappings(); loadFormatName(); }, [loadMappings, loadFormatName]);

  const handleAdd = async (fd: AddFD) => {
    try {
      await apiClient.post('/masters/format-stage-mappings', {
        format_id: Number(formatId), stage_id: fd.stage_id, is_active: fd.is_active,
      });
      toast.current?.show({ severity: 'success', summary: 'Stage added', life: 3000 });
      setAddVisible(false);
      loadMappings();
    } catch (e: any) {
      toast.current?.show({ severity: 'error', summary: 'Error', detail: e?.response?.data?.detail || 'Failed', life: 5000 });
    }
  };

  const handleDelete = async (id: number) => {
    try {
      await apiClient.delete(`/masters/format-stage-mappings/${id}`);
      toast.current?.show({ severity: 'success', summary: 'Deleted', life: 3000 });
      loadMappings();
    } catch (e: any) {
      toast.current?.show({ severity: 'error', summary: 'Error', detail: e?.response?.data?.detail || 'Failed', life: 5000 });
    }
  };

  return (
    <div className="p-3">
      <Toast ref={toast} />
      <div className="flex align-items-center gap-2 mb-3">
        <Button icon="pi pi-arrow-left" severity="secondary" text
          onClick={() => navigate('/masters/formats-view')} type="button" />
        <div>
          <h2 className="text-xl font-semibold text-900 m-0">{formatName || 'Loading...'}</h2>
          <p className="text-600 mt-1 mb-0">Stages mapped to this format</p>
        </div>
      </div>

      <div className="surface-card p-3 border-round shadow-1">
        <div className="flex gap-2 mb-3">
          <Button label="Add Stage" icon="pi pi-plus" size="small"
            onClick={() => { reset({ stage_id: 0, is_active: true }); setAddVisible(true); }} type="button" />
        </div>

        <DataTable value={mappings} loading={loading} size="small" stripedRows
          emptyMessage="No stages mapped to this format.">
          <Column header="Stage" body={(row: FormatStageMapping) => stageMap[row.stage_id] ?? row.stage_id} />
          <Column header="Actions" body={(row: FormatStageMapping) => (
            <MasterRowActions label="mapping" canUpdate={false} canDelete={true}
              onEdit={() => {}} onDelete={() => handleDelete(row.id)} />
          )} style={{ width: '5rem' }} />
        </DataTable>
      </div>

      {/* Add Stage Dialog */}
      <Dialog header="Add Stage" visible={addVisible}
        onHide={() => setAddVisible(false)} style={{ width: '380px' }} modal
        footer={
          <div className="flex justify-content-end gap-2">
            <Button label="Cancel" severity="secondary" outlined onClick={() => setAddVisible(false)} type="button" />
            <Button label="Save" onClick={handleSubmit(handleAdd)} type="button" />
          </div>
        }
      >
        <form className="flex flex-column gap-3 pt-2" onSubmit={(e) => e.preventDefault()}>
          <div className="flex flex-column gap-2">
            <label className="font-medium text-sm">Stage <span className="p-error">*</span></label>
            <Controller name="stage_id" control={control} render={({ field }) => (
              <Dropdown value={field.value || null} options={stageOptions}
                onChange={(e) => field.onChange(e.value)} placeholder="Select Stage"
                filter className="w-full" />
            )} />
          </div>
          <div className="flex align-items-center gap-3">
            <Controller name="is_active" control={control} render={({ field }) => (
              <InputSwitch checked={field.value} onChange={(e) => field.onChange(e.value)} />
            )} />
            <label className="font-medium text-sm">Active</label>
          </div>
        </form>
      </Dialog>
    </div>
  );
};
