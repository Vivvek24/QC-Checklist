import { useState, useEffect } from 'react';
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
import { useSapFields, useCreateSapField, useUpdateSapField, useDeleteSapField } from '../hooks/useSapFields';
import { useMasterCrudController } from '../hooks/useMasterCrudController';
import { useMasterPermissions } from '../hooks/useMasterPermissions';
import type { SapField, CreateSapFieldRequest } from '../models/SapField';

const schema = z.object({ field_name: z.string().min(1).max(255), is_active: z.boolean() });
type FD = z.infer<typeof schema>;
const EMPTY: FD = { field_name: '', is_active: true };

const Form = ({ visible, item, saving, onHide, onSubmit }: { visible: boolean; item: SapField | null; saving?: boolean; onHide: () => void; onSubmit: (d: CreateSapFieldRequest) => void }) => {
  const isEdit = Boolean(item);
  const { register, handleSubmit, control, reset, formState: { errors } } = useForm<FD>({ resolver: zodResolver(schema), defaultValues: EMPTY });
  useEffect(() => { if (visible) reset(item ? { field_name: item.field_name, is_active: item.is_active } : EMPTY); }, [visible, item, reset]);
  const close = () => { reset(EMPTY); onHide(); };
  return (
    <Dialog header={isEdit ? `Edit — ${item?.field_name}` : 'New SAP Field'} visible={visible} onHide={close} style={{ width: '420px' }} modal
      footer={<div className="flex justify-content-end gap-2"><Button label="Cancel" severity="secondary" outlined onClick={close} /><Button label={isEdit ? 'Save' : 'Create'} loading={saving} onClick={handleSubmit((d) => onSubmit({ field_name: d.field_name.trim(), is_active: d.is_active }))} /></div>}>
      <form className="flex flex-column gap-4 pt-3">
        <div className="flex flex-column gap-2"><label className="font-medium text-sm">Field Name *</label><InputText {...register('field_name')} className={errors.field_name ? 'p-invalid' : ''} />{errors.field_name && <small className="p-error">{errors.field_name.message}</small>}</div>
        <div className="flex align-items-center gap-3"><Controller name="is_active" control={control} render={({ field }) => <InputSwitch checked={field.value} onChange={(e) => field.onChange(e.value)} />} /><label className="font-medium text-sm">Active</label></div>
      </form>
    </Dialog>
  );
};

export const SapFieldPage = () => {
  const [filters, setFilters] = useState<DataTableFilterMeta>({ field_name: { value: null, matchMode: FilterMatchMode.CONTAINS } });
  const { data, isLoading, refetch, isRefetching } = useSapFields();
  const c = useCreateSapField(), u = useUpdateSapField(), d = useDeleteSapField();
  const perms = useMasterPermissions('sap_fields');
  const crud = useMasterCrudController<SapField, CreateSapFieldRequest>({ entityLabel: 'SAP Field', labelOf: (r) => r.field_name, onCreate: (r) => c.mutateAsync(r), onUpdate: (id, r) => u.mutateAsync({ id, request: r }), onDelete: (id) => d.mutateAsync(id) });
  return (
    <MasterCrudPage<SapField> title="SAP Fields" subtitle="Manage SAP field master" newLabel="New SAP Field"
      rows={data?.items ?? []} loading={isLoading || isRefetching} refreshing={isRefetching} onRefresh={() => refetch()} onNew={crud.openCreate} canCreate={perms.canCreate}
      filters={filters} onFilterChange={setFilters} emptyMessage="No SAP fields yet." toastRef={crud.toast}
      columns={<><Column field="field_name" header="Field Name" sortable filter filterPlaceholder="Search..." /><Column header="Status" body={(r: SapField) => <MasterStatusTag isActive={r.is_active} />} style={{ width: '8rem' }} />{perms.canModifyRows && <Column header="Actions" body={(r: SapField) => <MasterRowActions label={r.field_name} canUpdate={perms.canUpdate} canDelete={perms.canDelete} onEdit={() => crud.openEdit(r)} onDelete={() => crud.requestDelete(r)} />} style={{ width: '7rem' }} />}</>}>
      <Form visible={crud.dialogVisible} item={crud.editing} saving={c.isPending || u.isPending} onHide={crud.closeDialog} onSubmit={crud.submit} />
    </MasterCrudPage>
  );
};
