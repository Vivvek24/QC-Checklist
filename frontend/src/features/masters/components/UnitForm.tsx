/**
 * Create / edit dialog for a Unit.
 * Includes a Business Unit dropdown.
 */

import { useEffect } from 'react';
import { zodResolver } from '@hookform/resolvers/zod';
import { Button } from 'primereact/button';
import { Dialog } from 'primereact/dialog';
import { Dropdown } from 'primereact/dropdown';
import { InputSwitch } from 'primereact/inputswitch';
import { InputText } from 'primereact/inputtext';
import { Controller, useForm } from 'react-hook-form';
import { z } from 'zod';
import { useBusinessUnits } from '../hooks/useBusinessUnits';
import type { Unit, CreateUnitRequest } from '../models/Unit';

const schema = z.object({
  name: z.string().min(1, 'Name is required').max(255),
  business_unit_id: z.number({ required_error: 'Business Unit is required' }).min(1, 'Business Unit is required'),
  is_active: z.boolean(),
});

type FormData = z.infer<typeof schema>;

const EMPTY: FormData = { name: '', business_unit_id: 0, is_active: true };

interface UnitFormProps {
  visible: boolean;
  unit: Unit | null;
  saving?: boolean;
  onHide: () => void;
  onSubmit: (data: CreateUnitRequest) => void;
}

export const UnitForm = ({ visible, unit, saving, onHide, onSubmit }: UnitFormProps) => {
  const isEdit = Boolean(unit);

  const { data: buData } = useBusinessUnits({ is_active: true });
  const businessUnitOptions = (buData?.items ?? []).map((bu) => ({
    label: bu.name,
    value: bu.id,
  }));

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
      unit
        ? { name: unit.name, business_unit_id: unit.business_unit_id, is_active: unit.is_active }
        : EMPTY
    );
  }, [visible, unit, reset]);

  const close = () => { reset(EMPTY); onHide(); };

  const submit = (data: FormData) => {
    onSubmit({ name: data.name.trim(), business_unit_id: data.business_unit_id, is_active: data.is_active });
  };

  return (
    <Dialog
      header={isEdit ? `Edit Unit — ${unit?.name}` : 'New Unit'}
      visible={visible}
      onHide={close}
      style={{ width: '440px' }}
      modal
      aria-label="Unit dialog"
      footer={
        <div className="flex justify-content-end gap-2">
          <Button label="Cancel" icon="pi pi-times" severity="secondary" outlined onClick={close} />
          <Button label={isEdit ? 'Save Changes' : 'Create'} icon="pi pi-check" loading={saving} onClick={handleSubmit(submit)} />
        </div>
      }
    >
      <form className="flex flex-column gap-4 pt-3">
        {/* Name */}
        <div className="flex flex-column gap-2">
          <label htmlFor="unit-name" className="font-medium">
            Name <span className="p-error">*</span>
          </label>
          <InputText
            id="unit-name"
            {...register('name')}
            placeholder="e.g. Procurement"
            className={errors.name ? 'p-invalid' : ''}
            aria-describedby="unit-name-error"
          />
          {errors.name && <small id="unit-name-error" className="p-error">{errors.name.message}</small>}
        </div>

        {/* Business Unit */}
        <div className="flex flex-column gap-2">
          <label htmlFor="unit-bu" className="font-medium">
            Business Unit <span className="p-error">*</span>
          </label>
          <Controller
            name="business_unit_id"
            control={control}
            render={({ field }) => (
              <Dropdown
                id="unit-bu"
                value={field.value || null}
                options={businessUnitOptions}
                onChange={(e) => field.onChange(e.value)}
                placeholder="Select Business Unit"
                filter
                className={errors.business_unit_id ? 'p-invalid' : ''}
                aria-describedby="unit-bu-error"
              />
            )}
          />
          {errors.business_unit_id && (
            <small id="unit-bu-error" className="p-error">{errors.business_unit_id.message}</small>
          )}
        </div>

        {/* Active toggle */}
        <div className="flex align-items-center gap-3">
          <Controller
            name="is_active"
            control={control}
            render={({ field }) => (
              <InputSwitch
                id="unit-active"
                checked={field.value}
                onChange={(e) => field.onChange(e.value)}
                aria-label="Unit active"
              />
            )}
          />
          <label htmlFor="unit-active" className="font-medium cursor-pointer">Active</label>
        </div>
      </form>
    </Dialog>
  );
};
