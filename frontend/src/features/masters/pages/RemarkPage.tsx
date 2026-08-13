import { useState, useEffect } from 'react';
import { FilterMatchMode } from 'primereact/api';
import { Column } from 'primereact/column';
import { Button } from 'primereact/button';
import { Dialog } from 'primereact/dialog';
import { MultiSelect } from 'primereact/multiselect';
import { InputSwitch } from 'primereact/inputswitch';
import { InputTextarea } from 'primereact/inputtextarea';
import { Controller, useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import type { DataTableFilterMeta } from 'primereact/datatable';
import { MasterCrudPage } from '../components/MasterCrudPage';
import { MasterRowActions } from '../components/MasterRowActions';
import { MasterStatusTag } from '../components/MasterStatusTag';
import { useRemarks, useCreateRemark, useUpdateRemark, useDeleteRemark } from '../hooks/useRemarks';
import { useMasterCrudController } from '../hooks/useMasterCrudController';
import { useMasterPermissions } from '../hooks/useMasterPermissions';
import { useRoles } from '@features/user-management/hooks/useRoles';
import type { Remark, CreateRemarkRequest } from '../models/Remark';

const schema = z.object({
  remark: z.string().min(1).max(2000),
  role_ids: z.array(z.number()).min(1, 'At least one role is required'),
  is_active: z.boolean(),
});
type FD = z.infer<typeof schema>;
const EMPTY: FD = { remark: '', role_ids: [], is_active: true };

const Form = ({ visible, item, saving, onHide, onSubmit }: {
  visible: boolean; item: Remark | null; saving?: boolean; onHide: () => void; onSubmit: (d: CreateRemarkRequest) => void;
}) => {
  const isEdit = Boolean(item);
  const { roleOptions } = useRoles();
  const { handleSubmit, control, reset, register, formState: { errors } } = useForm<FD>({
    resolver: zodResolver(schema), defaultValues: EMPTY,
  });
  useEffect(() => {
    if (visible) reset(item ? { remark: item.remark, role_ids: item.role_ids, is_active: item.is_active } : EMPTY);
  }, [visible, item, reset]);
  const close = () => { reset(EMPTY); onHide(); };
  return (
    <Dialog header={isEdit ? 'Edit Remark' : 'New Remark'} visible={visible} onHide={close}
      style={{ width: '480px' }} modal
      footer={
        <div className="flex justify-content-end gap-2">
          <Button label="Cancel" severity="secondary" outlined onClick={close} />
          <Button label={isEdit ? 'Save' : 'Create'} loading={saving}
            onClick={handleSubmit((d) => onSubmit({ remark: d.remark.trim(), role_ids: d.role_ids, is_active: d.is_active }))} />
        </div>
      }
    >
      <form className="flex flex-column gap-3 pt-3">
        <div className="flex flex-column gap-2">
          <label className="font-medium text-sm">Remark <span className="p-error">*</span></label>
          <InputTextarea {...register('remark')} rows={3} autoResize className={errors.remark ? 'p-invalid' : ''} />
          {errors.remark && <small className="p-error">{errors.remark.message}</small>}
        </div>
        <div className="flex flex-column gap-2">
          <label className="font-medium text-sm">User Roles <span className="p-error">*</span></label>
          <Controller name="role_ids" control={control} render={({ field }) => (
            <MultiSelect
              value={field.value}
              options={roleOptions}
              onChange={(e) => field.onChange(e.value)}
              placeholder="Select roles"
              filter
              display="chip"
              className={errors.role_ids ? 'p-invalid w-full' : 'w-full'}
            />
          )} />
          {errors.role_ids && <small className="p-error">{errors.role_ids.message}</small>}
        </div>
        <div className="flex align-items-center gap-3">
          <Controller name="is_active" control={control} render={({ field }) => (
            <InputSwitch checked={field.value} onChange={(e) => field.onChange(e.value)} />
          )} />
          <label className="font-medium text-sm">Active</label>
        </div>
      </form>
    </Dialog>
  );
};

export const RemarkPage = () => {
  const [filters, setFilters] = useState<DataTableFilterMeta>({ remark: { value: null, matchMode: FilterMatchMode.CONTAINS } });
  const { data, isLoading, refetch, isRefetching } = useRemarks();
  const { roleOptions } = useRoles();
  const roleMap = Object.fromEntries(roleOptions.map((r) => [r.value, r.label]));
  const c = useCreateRemark(), u = useUpdateRemark(), d = useDeleteRemark();
  const perms = useMasterPermissions('remarks');
  const crud = useMasterCrudController<Remark, CreateRemarkRequest>({
    entityLabel: 'Remark', labelOf: (r) => r.remark.slice(0, 30),
    onCreate: (r) => c.mutateAsync(r),
    onUpdate: (id, r) => u.mutateAsync({ id, request: r }),
    onDelete: (id) => d.mutateAsync(id),
  });
  return (
    <MasterCrudPage<Remark>
      title="Remarks" subtitle="Manage remark master" newLabel="New Remark"
      rows={data?.items ?? []} loading={isLoading || isRefetching} refreshing={isRefetching}
      onRefresh={() => refetch()} onNew={crud.openCreate} canCreate={perms.canCreate}
      filters={filters} onFilterChange={setFilters} emptyMessage="No remarks yet." toastRef={crud.toast}
      columns={
        <>
          <Column field="remark" header="Remark" sortable filter filterPlaceholder="Search..." />
          <Column header="Roles" body={(r: Remark) => r.role_ids.map(id => roleMap[id] ?? id).join(', ') || '—'} style={{ width: '14rem' }} />
          <Column header="Status" body={(r: Remark) => <MasterStatusTag isActive={r.is_active} />} style={{ width: '8rem' }} />
          {perms.canModifyRows && (
            <Column header="Actions" body={(r: Remark) => (
              <MasterRowActions label={r.remark.slice(0, 20)} canUpdate={perms.canUpdate} canDelete={perms.canDelete}
                onEdit={() => crud.openEdit(r)} onDelete={() => crud.requestDelete(r)} />
            )} style={{ width: '7rem' }} />
          )}
        </>
      }
    >
      <Form visible={crud.dialogVisible} item={crud.editing}
        saving={c.isPending || u.isPending} onHide={crud.closeDialog} onSubmit={crud.submit} />
    </MasterCrudPage>
  );
};
