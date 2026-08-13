import { useCallback, useEffect, useState } from 'react';
import { zodResolver } from '@hookform/resolvers/zod';
import { Button } from 'primereact/button';
import { Dialog } from 'primereact/dialog';
import { InputSwitch } from 'primereact/inputswitch';
import { InputText } from 'primereact/inputtext';
import { MultiSelect } from 'primereact/multiselect';
import { DataTable } from 'primereact/datatable';
import { Column } from 'primereact/column';
import { Tag } from 'primereact/tag';
import { Controller, useForm } from 'react-hook-form';
import { z } from 'zod';
import { approvalLabelApi } from '../api/approvalLabelApi';
import { useRoles } from '@features/user-management/hooks/useRoles';
import { MasterRowActions } from './MasterRowActions';
import { MenuGate } from '@core/rbac';
import type { Stage, CreateStageRequest } from '../models/Stage';

interface LocalLabel {
  tempId: string;
  id?: number;
  label: string;
  role_ids: number[];
  is_active: boolean;
}

const schema = z.object({
  stage_name: z.string().min(1, 'Stage Name is required').max(255),
  is_active: z.boolean(),
});
type FormData = z.infer<typeof schema>;
const EMPTY: FormData = { stage_name: '', is_active: true };

const labelSchema = z.object({
  label: z.string().min(1, 'Label is required').max(255),
  role_ids: z.array(z.number()),
  is_active: z.boolean(),
});
type LabelFD = z.infer<typeof labelSchema>;
const LABEL_EMPTY: LabelFD = { label: '', role_ids: [], is_active: true };

export interface StageSubmitPayload extends CreateStageRequest {
  approval_labels: { id?: number; label: string; role_ids: number[]; is_active: boolean }[];
}

interface StageFormProps {
  visible: boolean;
  stage: Stage | null;
  saving?: boolean;
  onHide: () => void;
  onSubmit: (data: StageSubmitPayload) => void;
}

let tempCounter = 0;

export const StageForm = ({ visible, stage, saving, onHide, onSubmit }: StageFormProps) => {
  const isEdit = Boolean(stage);
  const stageId = stage ? Number(stage.id) : undefined;

  const { register, handleSubmit, control, reset, formState: { errors } } = useForm<FormData>({
    resolver: zodResolver(schema), defaultValues: EMPTY,
  });

  const [localLabels, setLocalLabels] = useState<LocalLabel[]>([]);
  const [labelDialogOpen, setLabelDialogOpen] = useState(false);
  const [editingIdx, setEditingIdx] = useState<number | null>(null);

  const { roleOptions } = useRoles();
  const roleMap = Object.fromEntries(roleOptions.map((r) => [r.value, r.label]));

  const {
    register: regLabel,
    handleSubmit: handleLabelSubmit,
    control: labelCtrl,
    reset: resetLabel,
    formState: { errors: labelErrors },
  } = useForm<LabelFD>({ resolver: zodResolver(labelSchema), defaultValues: LABEL_EMPTY });

  const [labelsLoaded, setLabelsLoaded] = useState(false);

  const loadLabels = useCallback(async (sid: number) => {
    try {
      const result = await approvalLabelApi.list({ stage_id: sid });
      setLocalLabels(result.items.map((l) => ({
        tempId: `ex-${l.id}`, id: Number(l.id),
        label: l.label, role_ids: l.role_ids, is_active: l.is_active,
      })));
    } catch { setLocalLabels([]); }
    setLabelsLoaded(true);
  }, []);

  useEffect(() => {
    if (!visible) {
      setLabelsLoaded(false);
      return;
    }
    reset(stage ? { stage_name: stage.stage_name, is_active: stage.is_active } : EMPTY);
    setLabelDialogOpen(false);
    setEditingIdx(null);
    if (stageId && !labelsLoaded) {
      loadLabels(stageId);
    } else if (!stageId) {
      setLocalLabels([]);
      setLabelsLoaded(true);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [visible]);

  const close = () => { reset(EMPTY); setLocalLabels([]); onHide(); };

  const openCreateLabel = () => {
    setEditingIdx(null);
    resetLabel(LABEL_EMPTY);
    setLabelDialogOpen(true);
  };

  const openEditLabel = (idx: number) => {
    const lbl = localLabels[idx]!;
    setEditingIdx(idx);
    resetLabel({ label: lbl.label, role_ids: lbl.role_ids, is_active: lbl.is_active });
    setLabelDialogOpen(true);
  };

  const deleteLabel = (idx: number) => setLocalLabels((prev) => prev.filter((_, i) => i !== idx));

  const saveLabelLocal = (data: LabelFD) => {
    if (editingIdx !== null) {
      setLocalLabels((prev) => prev.map((l, i) => i === editingIdx
        ? { ...l, label: data.label.trim(), role_ids: data.role_ids, is_active: data.is_active }
        : l));
    } else {
      setLocalLabels((prev) => [...prev, {
        tempId: `new-${++tempCounter}`, label: data.label.trim(), role_ids: data.role_ids, is_active: data.is_active,
      }]);
    }
    setLabelDialogOpen(false);
    setEditingIdx(null);
  };

  const closeLabelDialog = () => { setLabelDialogOpen(false); setEditingIdx(null); };

  const handleFormSubmit = (data: FormData) => {
    onSubmit({
      stage_name: data.stage_name.trim(), is_active: data.is_active,
      approval_labels: localLabels.map((l) => ({ id: l.id, label: l.label, role_ids: l.role_ids, is_active: l.is_active })),
    });
  };

  return (
    <>
      {/* Parent Stage Dialog — always visible when `visible` prop is true */}
      <Dialog header={isEdit ? `Edit Stage — ${stage?.stage_name}` : 'New Stage'}
        visible={visible} onHide={() => { if (!labelDialogOpen) close(); }}
        style={{ width: '650px' }} modal dismissableMask={false}
        closeOnEscape={!labelDialogOpen}
        aria-label="Stage dialog"
        footer={
          <div className="flex justify-content-end gap-2">
            <Button label="Cancel" icon="pi pi-times" severity="secondary" outlined onClick={() => { if (!labelDialogOpen) close(); }} />
            <Button label={isEdit ? 'Save Changes' : 'Create'} icon="pi pi-check" loading={saving}
              onClick={handleSubmit(handleFormSubmit)} />
          </div>
        }
      >
        <form className="flex flex-column gap-4 pt-3" onSubmit={(e) => e.preventDefault()}>
          <div className="flex flex-column gap-2">
            <label htmlFor="stage-name" className="font-medium text-sm">Stage Name <span className="p-error">*</span></label>
            <InputText id="stage-name" {...register('stage_name')} placeholder="e.g. Dispensing" className={errors.stage_name ? 'p-invalid' : ''} />
            {errors.stage_name && <small className="p-error">{errors.stage_name.message}</small>}
          </div>

          <MenuGate menuKey="masters.approval_labels">
            <div className="flex flex-column gap-2">
              <Button type="button" label="Add Approval Label" icon="pi pi-plus" size="small"
                outlined onClick={openCreateLabel} className="align-self-start" />
              {localLabels.length > 0 && (
                <DataTable value={localLabels} size="small" stripedRows
                  emptyMessage="No approval labels." style={{ fontSize: '0.78rem' }}>
                  <Column field="label" header="Label" />
                  <Column header="Roles" body={(row: LocalLabel) =>
                    row.role_ids.map((id) => roleMap[id] ?? id).join(', ') || '—'
                  } />
                  <Column header="Status" body={(row: LocalLabel) => (
                    <Tag value={row.is_active ? 'Active' : 'Inactive'} severity={row.is_active ? 'success' : 'warning'} />
                  )} style={{ width: '6rem' }} />
                  <Column header="Actions" body={(_row: LocalLabel, opts) => (
                    <MasterRowActions label={_row.label} canUpdate={true} canDelete={true}
                      onEdit={() => openEditLabel(opts.rowIndex)} onDelete={() => deleteLabel(opts.rowIndex)} />
                  )} style={{ width: '6rem' }} />
                </DataTable>
              )}
            </div>
          </MenuGate>

          <div className="flex align-items-center gap-3">
            <Controller name="is_active" control={control} render={({ field }) => (
              <InputSwitch id="stage-active" checked={field.value} onChange={(e) => field.onChange(e.value)} aria-label="Active" />
            )} />
            <label htmlFor="stage-active" className="font-medium text-sm cursor-pointer">Active</label>
          </div>
        </form>
      </Dialog>

      {/* Child Label Dialog — opens on TOP of parent, no mask conflict */}
      <Dialog
        header={editingIdx !== null ? 'Edit Approval Label' : 'Add Approval Label'}
        visible={labelDialogOpen}
        onHide={closeLabelDialog}
        style={{ width: '420px', zIndex: 1100 }}
        modal={false}
        closable
        dismissableMask={false}
        className="p-dialog-top"
        footer={
          <div className="flex justify-content-end gap-2">
            <Button label="Cancel" severity="secondary" outlined onClick={closeLabelDialog} />
            <Button label={editingIdx !== null ? 'Save' : 'Add'}
              onClick={handleLabelSubmit(saveLabelLocal)} />
          </div>
        }
      >
        <form className="flex flex-column gap-3 pt-3">
          <div className="flex flex-column gap-2">
            <label className="font-medium text-sm">Label <span className="p-error">*</span></label>
            <InputText {...regLabel('label')} placeholder="e.g. Level 1 Approval"
              className={labelErrors.label ? 'p-invalid' : ''} />
            {labelErrors.label && <small className="p-error">{labelErrors.label.message}</small>}
          </div>
          <div className="flex flex-column gap-2">
            <label className="font-medium text-sm">User Roles</label>
            <Controller name="role_ids" control={labelCtrl} render={({ field }) => (
              <MultiSelect value={field.value} options={roleOptions}
                onChange={(e) => field.onChange(e.value)} placeholder="Select roles"
                filter display="chip" className="w-full" />
            )} />
          </div>
          <div className="flex align-items-center gap-3">
            <Controller name="is_active" control={labelCtrl} render={({ field }) => (
              <InputSwitch checked={field.value} onChange={(e) => field.onChange(e.value)} />
            )} />
            <label className="font-medium text-sm">Active</label>
          </div>
        </form>
      </Dialog>
    </>
  );
};
