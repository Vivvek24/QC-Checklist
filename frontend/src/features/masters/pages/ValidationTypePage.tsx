import { useState } from 'react';
import { FilterMatchMode } from 'primereact/api';
import { Column } from 'primereact/column';
import { Button } from 'primereact/button';
import { Dialog } from 'primereact/dialog';
import { InputSwitch } from 'primereact/inputswitch';
import { InputText } from 'primereact/inputtext';
import { Controller, useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import type { DataTableFilterMeta } from 'primereact/datatable';
import { MasterCrudPage } from '../components/MasterCrudPage';
import { MasterRowActions } from '../components/MasterRowActions';
import { MasterStatusTag } from '../components/MasterStatusTag';
import { useValidationTypes, useCreateValidationType, useUpdateValidationType, useDeleteValidationType } from '../hooks/useValidationTypes';
import { useMasterCrudController } from '../hooks/useMasterCrudController';
import { useMasterPermissions } from '../hooks/useMasterPermissions';
import type { ValidationType, CreateValidationTypeRequest } from '../models/ValidationType';
import { useEffect } from 'react';

const schema = z.object({ name: z.string().min(1).max(255), is_active: z.boolean() });
type FD = z.infer<typeof schema>;
const EMPTY: FD = { name: '', is_active: true };

const Form = ({ visible, item, saving, onHide, onSubmit }: { visible: boolean; item: ValidationType | null; saving?: boolean; onHide: () => void; onSubmit: (d: CreateValidationTypeRequest) => void }) => {
  const isEdit = Boolean(item);
  const { register, handleSubmit, control, reset, formState: { errors } } = useForm<FD>({ resolver: zodResolver(schema), defaultValues: EMPTY });
  useEffect(() => { if (visible) reset(item ? { name: item.name, is_active: item.is_active } : EMPTY); }, [visible, item, reset]);
  const close = () => { reset(EMPTY); onHide(); };
  return (
    <Dialog header={isEdit ? `Edit — ${item?.name}` : 'New Validation Type'} visible={visible} onHide={close} style={{ width: '420px' }} modal
      footer={<div className="flex justify-content-end gap-2"><Button label="Cancel" severity="secondary" outlined onClick={close} /><Button label={isEdit ? 'Save' : 'Create'} loading={saving} onClick={handleSubmit((d) => onSubmit({ name: d.name.trim(), is_active: d.is_active }))} /></div>}>
      <form className="flex flex-column gap-4 pt-3">
        <div className="flex flex-column gap-2"><label className="font-medium text-sm">Name *</label><InputText {...register('name')} className={errors.name ? 'p-invalid' : ''} />{errors.name && <small className="p-error">{errors.name.message}</small>}</div>
        <div className="flex align-items-center gap-3"><Controller name="is_active" control={control} render={({ field }) => <InputSwitch checked={field.value} onChange={(e) => field.onChange(e.value)} />} /><label className="font-medium text-sm">Active</label></div>
      </form>
    </Dialog>
  );
};

export const ValidationTypePage = () => {
  const [filters, setFilters] = useState<DataTableFilterMeta>({ name: { value: null, matchMode: FilterMatchMode.CONTAINS } });
  const { data, isLoading, refetch, isRefetching } = useValidationTypes();
  const c = useCreateValidationType(), u = useUpdateValidationType(), d = useDeleteValidationType();
  const perms = useMasterPermissions('validation_types');
  const crud = useMasterCrudController<ValidationType, CreateValidationTypeRequest>({ entityLabel: 'Validation Type', labelOf: (r) => r.name, onCreate: (r) => c.mutateAsync(r), onUpdate: (id, r) => u.mutateAsync({ id, request: r }), onDelete: (id) => d.mutateAsync(id) });
  return (
    <MasterCrudPage<ValidationType> title="Validation Types" subtitle="Manage validation type master" newLabel="New Validation Type"
      rows={data?.items ?? []} loading={isLoading || isRefetching} refreshing={isRefetching} onRefresh={() => refetch()} onNew={crud.openCreate} canCreate={perms.canCreate}
      filters={filters} onFilterChange={setFilters} emptyMessage="No validation types yet." toastRef={crud.toast}
      columns={<><Column field="name" header="Name" sortable filter filterPlaceholder="Search..." /><Column header="Status" body={(r: ValidationType) => <MasterStatusTag isActive={r.is_active} />} style={{ width: '8rem' }} />{perms.canModifyRows && <Column header="Actions" body={(r: ValidationType) => <MasterRowActions label={r.name} canUpdate={perms.canUpdate} canDelete={perms.canDelete} onEdit={() => crud.openEdit(r)} onDelete={() => crud.requestDelete(r)} />} style={{ width: '7rem' }} />}</>}>
      <Form visible={crud.dialogVisible} item={crud.editing} saving={c.isPending || u.isPending} onHide={crud.closeDialog} onSubmit={crud.submit} />
    </MasterCrudPage>
  );
};
