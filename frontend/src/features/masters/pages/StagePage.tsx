import { useRef, useState } from 'react';
import { FilterMatchMode } from 'primereact/api';
import { Column } from 'primereact/column';
import { Toast } from 'primereact/toast';
import type { DataTableFilterMeta } from 'primereact/datatable';
import { StageForm, type StageSubmitPayload } from '../components/StageForm';
import { MasterCrudPage } from '../components/MasterCrudPage';
import { MasterRowActions } from '../components/MasterRowActions';
import { MasterStatusTag } from '../components/MasterStatusTag';
import { useStages, useCreateStage, useUpdateStage, useDeleteStage } from '../hooks/useStages';
import { useCreateApprovalLabel, useUpdateApprovalLabel, useDeleteApprovalLabel } from '../hooks/useApprovalLabels';
import { useMasterPermissions } from '../hooks/useMasterPermissions';
import type { Stage } from '../models/Stage';

const defaultFilters: DataTableFilterMeta = {
  stage_name: { value: null, matchMode: FilterMatchMode.CONTAINS },
};

export const StagePage = () => {
  const [filters, setFilters] = useState<DataTableFilterMeta>(defaultFilters);
  const { data, isLoading, refetch, isRefetching } = useStages();
  const createMutation = useCreateStage();
  const updateMutation = useUpdateStage();
  const deleteMutation = useDeleteStage();
  const createLabel = useCreateApprovalLabel();
  const updateLabel = useUpdateApprovalLabel();
  const deleteLabel = useDeleteApprovalLabel();
  const permissions = useMasterPermissions('stages');

  const toast = useRef<Toast>(null);
  const [dialogVisible, setDialogVisible] = useState(false);
  const [editing, setEditing] = useState<Stage | null>(null);
  const [formSaving, setFormSaving] = useState(false);

  const openCreate = () => { setEditing(null); setDialogVisible(true); };
  const openEdit = (row: Stage) => { setEditing(row); setDialogVisible(true); };
  const closeDialog = () => { setDialogVisible(false); setEditing(null); };

  const handleDelete = async (row: Stage) => {
    try {
      await deleteMutation.mutateAsync(String(row.id));
      toast.current?.show({ severity: 'success', summary: 'Deleted', detail: `Stage '${row.stage_name}' deleted`, life: 3000 });
    } catch (e: any) {
      toast.current?.show({ severity: 'error', summary: 'Error', detail: e?.response?.data?.detail || 'Delete failed', life: 5000 });
    }
  };

  const handleSubmit = async (payload: StageSubmitPayload) => {
    setFormSaving(true);
    try {
      let stageId: number;
      if (editing) {
        await updateMutation.mutateAsync({ id: String(editing.id), request: { stage_name: payload.stage_name, is_active: payload.is_active } });
        stageId = Number(editing.id);
      } else {
        const created = await createMutation.mutateAsync({ stage_name: payload.stage_name, is_active: payload.is_active });
        stageId = Number((created as any).id);
      }

      // Sync approval labels using existing API
      // Get current labels from server for this stage
      const existingIds = new Set(
        payload.approval_labels.filter((l) => l.id).map((l) => l.id!)
      );

      // Delete labels that were removed (only in edit mode)
      if (editing) {
        const { data: serverLabels } = await import('@shared/services/apiClient').then((m) =>
          m.apiClient.get<{ items: { id: number }[] }>('/masters/approval-labels', { params: { stage_id: stageId } })
        );
        for (const sl of serverLabels.items) {
          if (!existingIds.has(sl.id)) {
            await deleteLabel.mutateAsync(String(sl.id));
          }
        }
      }

      // Create or update each label
      for (const lbl of payload.approval_labels) {
        if (lbl.id) {
          await updateLabel.mutateAsync({ id: String(lbl.id), request: { label: lbl.label, role_ids: lbl.role_ids, is_active: lbl.is_active } });
        } else {
          await createLabel.mutateAsync({ label: lbl.label, stage_id: stageId, role_ids: lbl.role_ids, is_active: lbl.is_active });
        }
      }

      toast.current?.show({ severity: 'success', summary: 'Success', detail: editing ? 'Stage updated' : 'Stage created', life: 3000 });
      closeDialog();
    } catch (e: any) {
      toast.current?.show({ severity: 'error', summary: 'Error', detail: e?.response?.data?.detail || 'Save failed', life: 5000 });
    } finally {
      setFormSaving(false);
    }
  };

  return (
    <MasterCrudPage<Stage>
      title="Stages" subtitle="Manage stage master data" newLabel="New Stage"
      rows={data?.items ?? []} loading={isLoading || isRefetching} refreshing={isRefetching}
      onRefresh={() => refetch()} onNew={openCreate} canCreate={permissions.canCreate}
      filters={filters} onFilterChange={setFilters} emptyMessage="No stages defined yet." toastRef={toast}
      columns={
        <>
          <Column field="stage_name" header="Stage Name" sortable filter filterPlaceholder="Search..." />
          <Column header="Status" body={(row: Stage) => <MasterStatusTag isActive={row.is_active} />} style={{ width: '8rem' }} />
          {permissions.canModifyRows && (
            <Column header="Actions" body={(row: Stage) => (
              <MasterRowActions label={row.stage_name} canUpdate={permissions.canUpdate} canDelete={permissions.canDelete}
                onEdit={() => openEdit(row)} onDelete={() => handleDelete(row)} />
            )} style={{ width: '7rem' }} />
          )}
        </>
      }
    >
      <StageForm visible={dialogVisible} stage={editing} saving={formSaving}
        onHide={closeDialog} onSubmit={handleSubmit} />
    </MasterCrudPage>
  );
};
