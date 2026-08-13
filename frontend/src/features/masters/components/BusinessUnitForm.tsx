/**
 * Create / edit dialog for a Business Unit.
 */

import { useEffect } from 'react';
import { zodResolver } from '@hookform/resolvers/zod';
import { Button } from 'primereact/button';
import { Dialog } from 'primereact/dialog';
import { InputSwitch } from 'primereact/inputswitch';
import { InputText } from 'primereact/inputtext';
import { Controller, useForm } from 'react-hook-form';
import { z } from 'zod';
import type { BusinessUnit, CreateBusinessUnitRequest } from '../models/BusinessUnit';

const schema = z.object({
  name: z.string().min(1, 'Name is required').max(255, 'Name must be at most 255 characters'),
  is_active: z.boolean(),
});

type FormData = z.infer<typeof schema>;

const EMPTY: FormData = { name: '', is_active: true };

interface BusinessUnitFormProps {
  visible: boolean;
  businessUnit: BusinessUnit | null;
  saving?: boolean;
  onHide: () => void;
  onSubmit: (data: CreateBusinessUnitRequest) => void;
}

export const BusinessUnitForm = ({
  visible,
  businessUnit,
  saving,
  onHide,
  onSubmit,
}: BusinessUnitFormProps) => {
  const isEdit = Boolean(businessUnit);

  const {
    register,
    handleSubmit,
    control,
    reset,
    formState: { errors },
  } = useForm<FormData>({ resolver: zodResolver(schema), defaultValues: EMPTY });

  useEffect(() => {
    if (!visible) return;
    reset(
      businessUnit
        ? { name: businessUnit.name, is_active: businessUnit.is_active }
        : EMPTY
    );
  }, [visible, businessUnit, reset]);

  const close = () => {
    reset(EMPTY);
    onHide();
  };

  const submit = (data: FormData) => {
    onSubmit({ name: data.name.trim(), is_active: data.is_active });
  };

  return (
    <Dialog
      header={isEdit ? `Edit Business Unit — ${businessUnit?.name}` : 'New Business Unit'}
      visible={visible}
      onHide={close}
      style={{ width: '420px' }}
      modal
      aria-label="Business Unit dialog"
      footer={
        <div className="flex justify-content-end gap-2">
          <Button
            label="Cancel"
            icon="pi pi-times"
            severity="secondary"
            outlined
            onClick={close}
          />
          <Button
            label={isEdit ? 'Save Changes' : 'Create'}
            icon="pi pi-check"
            loading={saving}
            onClick={handleSubmit(submit)}
          />
        </div>
      }
    >
      <form className="flex flex-column gap-4 pt-3">
        <div className="flex flex-column gap-2">
          <label htmlFor="bu-name" className="font-medium">
            Name <span className="p-error">*</span>
          </label>
          <InputText
            id="bu-name"
            {...register('name')}
            placeholder="e.g. Sales & Marketing"
            className={errors.name ? 'p-invalid' : ''}
            aria-describedby="bu-name-error"
          />
          {errors.name && (
            <small id="bu-name-error" className="p-error">
              {errors.name.message}
            </small>
          )}
        </div>

        <div className="flex align-items-center gap-3">
          <Controller
            name="is_active"
            control={control}
            render={({ field }) => (
              <InputSwitch
                id="bu-active"
                checked={field.value}
                onChange={(e) => field.onChange(e.value)}
                aria-label="Business Unit active"
              />
            )}
          />
          <label htmlFor="bu-active" className="font-medium cursor-pointer">
            Active
          </label>
        </div>
      </form>
    </Dialog>
  );
};
