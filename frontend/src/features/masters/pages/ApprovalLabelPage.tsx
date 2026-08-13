import { useState } from 'react';
import { FilterMatchMode } from 'primereact/api';
import { Column } from 'primereact/column';
import type { DataTableFilterMeta } from 'primereact/datatable';
import { MasterCrudPage } from '../components/MasterCrudPage';
import { MasterRowActions } from '../components/MasterRowActions';
import { MasterStatusTag } from '../components/MasterStatusTag';
import { ApprovalLabelForm, type ApprovalLabelFormData } from '../components/ApprovalLabelForm';
import {
  useApprovalLabels,
  useCreateApprovalLabel,
  useUpdateApprovalLabel,
  useDeleteApprovalLabel,
} from '../hooks/useApprovalLabels';
import { useStages } from '../hooks/useStages';
import { useMasterPermissions } from '../hooks/useMasterPermissions';
import { useRoles } from '@features/user-management/hooks/useRoles';
import type { ApprovalLabel } from '../models/ApprovalLabel';
import { useRef } from 'react';
import { Toast } from 'primereact/toast';

export const ApprovalLabelPage = () => {
  const [filters, setFilters] = useState<DataTableFilterMeta>({
    label: { value: null, matchMode: FilterMatchMode.CONTAINS },
  });
  const { data, isLoading, refetch, isRefetching } = useApprovalLabels();
  const { data: stagesData } = useStages();
  const { roleOptions } = useRoles();

  const stageMap = Object.fromEntries((stagesData?.items ?? []).map((s) => [Number(s.id), s.stage_name]));
  const roleMap = Object.fromEntries(roleOptions.map((r) => [r.value, r.label]));

  const createMutation = useCreateApprovalLabel();
  const updateMutation = useUpdateApprovalLabel();
  const deleteMutation = useDeleteApprovalLabel();
  const perms = useMasterPermissions('approval_labels');
  const toast = useRef<Toast>(null);

  const [dialogVisible, setDialogVisible] = useState(false);
  const [editing, setEditing] = useState<ApprovalLabel | null>(null);

  const openCreate = () => { setEditing(null); setDialogVisible(true); };
  const openEdit = (row: ApprovalLabel) => { setEditing(row); setDialogVisible(true); };
  const closeDialog = () => { setDialogVisible(false); setEditing(null); };

  const handleSubmit = async (formData: ApprovalLabelFormData) => {
    try {
      if (editing) {
        await updateMutation.mutateAsync({
          id: String(editing.id),
          request: { label: formData.label, role_ids: formData.role_ids, is_active: formData.is_active, stage_id: formData.stage_id },
        });
        toast.current?.show({ severity: 'success', summary: 'Updated', life: 3000 });
      } else {
        await createMutation.mutateAsync({
          label: formData.label,
          stage_id: formData.stage_id!,
          role_ids: formData.role_ids,
          is_active: formData.is_active,
        });
        toast.current?.show({ severity: 'success', summary: 'Created', life: 3000 });
      }
      closeDialog();
    } catch (e: any) {
      toast.current?.show({ severity: 'error', summary: 'Error', detail: e?.response?.data?.detail || 'Failed', life: 5000 });
    }
  };

  const handleDelete = async (row: ApprovalLabel) => {
    try {
      await deleteMutation.mutateAsync(String(row.id));
      toast.current?.show({ severity: 'success', summary: 'Deleted', life: 3000 });
    } catch (e: any) {
      toast.current?.show({ severity: 'error', summary: 'Error', detail: e?.response?.data?.detail || 'Failed', life: 5000 });
    }
  };

  const editInitialData: ApprovalLabelFormData | null = editing
    ? { label: editing.label, role_ids: editing.role_ids, is_active: editing.is_active, stage_id: Number(editing.stage_id) }
    : null;

  return (
    <MasterCrudPage<ApprovalLabel>
      title="Approval Labels" subtitle="Manage approval label master" newLabel="New Approval Label"
      rows={data?.items ?? []} loading={isLoading || isRefetching} refreshing={isRefetching}
      onRefresh={() => refetch()} onNew={openCreate} canCreate={perms.canCreate}
      filters={filters} onFilterChange={setFilters} emptyMessage="No approval labels yet." toastRef={toast}
      columns={
        <>
          <Column field="label" header="Label" sortable filter filterPlaceholder="Search..." />
          <Column header="Stage" body={(r: ApprovalLabel) => stageMap[Number(r.stage_id)] ?? '—'} style={{ width: '12rem' }} />
          <Column header="Roles" body={(r: ApprovalLabel) => r.role_ids.map((id) => roleMap[id] ?? id).join(', ') || '—'} style={{ width: '14rem' }} />
          <Column header="Status" body={(r: ApprovalLabel) => <MasterStatusTag isActive={r.is_active} />} style={{ width: '8rem' }} />
          {perms.canModifyRows && (
            <Column header="Actions" body={(r: ApprovalLabel) => (
              <MasterRowActions label={r.label} canUpdate={perms.canUpdate} canDelete={perms.canDelete}
                onEdit={() => openEdit(r)} onDelete={() => handleDelete(r)} />
            )} style={{ width: '7rem' }} />
          )}
        </>
      }
    >
      <ApprovalLabelForm
        visible={dialogVisible}
        initialData={editInitialData}
        showStageField={true}
        saving={createMutation.isPending || updateMutation.isPending}
        onHide={closeDialog}
        onSubmit={handleSubmit}
      />
    </MasterCrudPage>
  );
};
