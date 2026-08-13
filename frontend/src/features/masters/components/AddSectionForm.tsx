/**
 * Add Section form dialog — simple section_name field.
 */

import { useEffect } from 'react';
import { zodResolver } from '@hookform/resolvers/zod';
import { Button } from 'primereact/button';
import { Dialog } from 'primereact/dialog';
import { InputText } from 'primereact/inputtext';
import { useForm } from 'react-hook-form';
import { z } from 'zod';

const schema = z.object({
  section_name: z.string().min(1, 'Section name is required').max(255),
});
type FD = z.infer<typeof schema>;
const EMPTY: FD = { section_name: '' };

interface Props {
  visible: boolean;
  saving?: boolean;
  onHide: () => void;
  onSubmit: (data: { section_name: string }) => void;
}

export const AddSectionForm = ({ visible, saving, onHide, onSubmit }: Props) => {
  const { register, handleSubmit, reset, formState: { errors } } = useForm<FD>({
    resolver: zodResolver(schema), defaultValues: EMPTY,
  });

  useEffect(() => { if (visible) reset(EMPTY); }, [visible, reset]);

  const close = () => { reset(EMPTY); onHide(); };

  return (
    <Dialog header="Add Section" visible={visible} onHide={close}
      style={{ width: '380px' }} modal
      footer={
        <div className="flex justify-content-end gap-2">
          <Button label="Cancel" severity="secondary" outlined onClick={close} type="button" />
          <Button label="Save" loading={saving} onClick={handleSubmit((d) => onSubmit(d))} type="button" />
        </div>
      }
    >
      <form className="flex flex-column gap-3 pt-2" onSubmit={(e) => e.preventDefault()}>
        <div className="flex flex-column gap-2">
          <label className="font-medium text-sm">Section Name <span className="p-error">*</span></label>
          <InputText {...register('section_name')} placeholder="e.g. Sampling Details"
            className={errors.section_name ? 'p-invalid' : ''} />
          {errors.section_name && <small className="p-error">{errors.section_name.message}</small>}
        </div>
      </form>
    </Dialog>
  );
};
