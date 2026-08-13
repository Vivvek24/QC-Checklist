/**
 * Approval Label form dialog — reusable popup for create/edit.
 * Used inside StageForm (inline label management) and ApprovalLabelPage.
 */

import { useEffect } from 'react';
import { zodResolver } from '@hookform/resolvers/zod';
import { Button } from 'primereact/button';
import { Dialog } from 'primereact/dialog';
import { InputSwitch } from 'primereact/inputswitch';
import { InputText } from 'primereact/inputtext';
import { MultiSelect } from 'primereact/multiselect';
import { Dropdown } from 'primereact/dropdown';
import { Controller, useForm } from 'react-hook-form';
import { z } from 'zod';
import { useRoles } from '@features/user-management/hooks/useRoles';
import { useStages } from '../hooks/useStages';

const schema = z.object({
  label: z.string().min(1, 'Label is required').max(255),
  role_ids: z.array(z.number()),
  is_active: z.boolean(),
  stage_id: z.number().optional(),
});
type FormData = z.infer<typeof schema>;
const EMPTY: FormData = { label: '', role_ids: [], is_active: true };

export interface ApprovalLabelFormData {
  label: string;
  role_ids: number[];
  is_active: boolean;
  stage_id?: number;
}

interface ApprovalLabelFormProps {
  visible: boolean;
  /** If provided, form is in edit mode with these values pre-filled */
  initialData?: ApprovalLabelFormData | null;
  /** Whether to show the stage dropdown (true for standalone page, false when embedded in StageForm) */
  showStageField?: boolean;
  saving?: boolean;
  /** When true, uses appendTo="self" to avoid overlay conflicts with parent dialog */
  nested?: boolean;
  onHide: () => void;
  onSubmit: (data: ApprovalLabelFormData) => void;
}

export const ApprovalLabelForm = ({
  visible,
  initialData,
  showStageField = false,
  saving,
  nested = false,
  onHide,
  onSubmit,
}: ApprovalLabelFormProps) => {
  const isEdit = Boolean(initialData);
  const { roleOptions } = useRoles();
  const { data: stagesData } = useStages();
  const stageOptions = (stagesData?.items ?? []).map((s) => ({ label: s.stage_name, value: Number(s.id) }));

  const { register, handleSubmit, control, reset, formState: { errors } } = useForm<FormData>({
    resolver: zodResolver(schema), defaultValues: EMPTY,
  });

  useEffect(() => {
    if (!visible) return;
    if (initialData) {
      reset({
        label: initialData.label,
        role_ids: initialData.role_ids,
        is_active: initialData.is_active,
        stage_id: initialData.stage_id,
      });
    } else {
      reset(EMPTY);
    }
  }, [visible, initialData, reset]);

  const close = () => { reset(EMPTY); onHide(); };

  const handleFormSubmit = (data: FormData) => {
    onSubmit({
      label: data.label.trim(),
      role_ids: data.role_ids,
      is_active: data.is_active,
      stage_id: data.stage_id,
    });
  };

  return (
    <Dialog
      header={isEdit ? 'Edit Approval Label' : 'Add Approval Label'}
      visible={visible}
      onHide={close}
      style={{ width: '420px' }}
      modal={!nested}
      blockScroll={!nested}
      dismissableMask={false}
      footer={
        <div className="flex justify-content-end gap-2">
          <Button label="Cancel" severity="secondary" outlined onClick={close} />
          <Button label={isEdit ? 'Save' : 'Add'} loading={saving}
            onClick={handleSubmit(handleFormSubmit)} />
        </div>
      }
    >
      <form className="flex flex-column gap-3 pt-3">
        <div className="flex flex-column gap-2">
          <label className="font-medium text-sm">Label <span className="p-error">*</span></label>
          <InputText {...register('label')} placeholder="e.g. Level 1 Approval"
            className={errors.label ? 'p-invalid' : ''} />
          {errors.label && <small className="p-error">{errors.label.message}</small>}
        </div>

        {showStageField && (
          <div className="flex flex-column gap-2">
            <label className="font-medium text-sm">Stage</label>
            <Controller name="stage_id" control={control} render={({ field }) => (
              <Dropdown value={field.value || null} options={stageOptions}
                onChange={(e) => field.onChange(e.value)} placeholder="Select stage"
                filter className="w-full" />
            )} />
          </div>
        )}

        <div className="flex flex-column gap-2">
          <label className="font-medium text-sm">User Roles</label>
          <Controller name="role_ids" control={control} render={({ field }) => (
            <MultiSelect value={field.value} options={roleOptions}
              onChange={(e) => field.onChange(e.value)} placeholder="Select roles"
              filter display="chip" className="w-full" />
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
  );
};
