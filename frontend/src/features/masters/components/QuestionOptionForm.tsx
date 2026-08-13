/**
 * Add/Edit Question Option popup dialog.
 */

import { useEffect } from 'react';
import { zodResolver } from '@hookform/resolvers/zod';
import { Button } from 'primereact/button';
import { Dialog } from 'primereact/dialog';
import { InputSwitch } from 'primereact/inputswitch';
import { InputText } from 'primereact/inputtext';
import { Controller, useForm } from 'react-hook-form';
import { z } from 'zod';
import type { QuestionOption } from '../models/QuestionOption';

const schema = z.object({
  option_title: z.string().min(1, 'Option title is required').max(500),
  is_active: z.boolean(),
});
type FD = z.infer<typeof schema>;
const EMPTY: FD = { option_title: '', is_active: true };

export interface QuestionOptionFormData {
  option_title: string;
  is_active: boolean;
}

interface Props {
  visible: boolean;
  initialData?: QuestionOption | null;
  saving?: boolean;
  onHide: () => void;
  onSubmit: (data: QuestionOptionFormData) => void;
}

export const QuestionOptionForm = ({ visible, initialData, saving, onHide, onSubmit }: Props) => {
  const isEdit = Boolean(initialData);
  const { register, handleSubmit, control, reset, formState: { errors } } = useForm<FD>({
    resolver: zodResolver(schema), defaultValues: EMPTY,
  });

  useEffect(() => {
    if (!visible) return;
    if (initialData) {
      reset({
        option_title: initialData.option_title,
        is_active: initialData.is_active,
      });
    } else {
      reset(EMPTY);
    }
  }, [visible, initialData, reset]);

  const close = () => { reset(EMPTY); onHide(); };

  return (
    <Dialog
      header={isEdit ? 'Edit Option' : 'Add Option'}
      visible={visible} onHide={close}
      style={{ width: '420px' }}
      modal={false} dismissableMask={false}
      footer={
        <div className="flex justify-content-end gap-2">
          <Button label="Cancel" severity="secondary" outlined onClick={close} type="button" />
          <Button label={isEdit ? 'Save' : 'Add'} loading={saving}
            onClick={handleSubmit((d) => onSubmit(d))} type="button" />
        </div>
      }
    >
      <form className="flex flex-column gap-3 pt-2" onSubmit={(e) => e.preventDefault()}>
        <div className="flex flex-column gap-2">
          <label className="font-medium text-sm">Option Title <span className="p-error">*</span></label>
          <InputText {...register('option_title')} placeholder="e.g. Option A"
            className={errors.option_title ? 'p-invalid' : ''} />
          {errors.option_title && <small className="p-error">{errors.option_title.message}</small>}
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
