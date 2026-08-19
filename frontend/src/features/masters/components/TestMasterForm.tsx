import { useEffect } from 'react';
import { zodResolver } from '@hookform/resolvers/zod';
import { Button } from 'primereact/button';
import { Dialog } from 'primereact/dialog';
import { InputSwitch } from 'primereact/inputswitch';
import { InputText } from 'primereact/inputtext';
import { InputNumber } from 'primereact/inputnumber';
import { Controller, useForm } from 'react-hook-form';
import { z } from 'zod';
import type { TestMaster, CreateTestMasterRequest } from '../models/TestMaster';

const schema = z.object({
  test_name: z.string().min(1, 'Test Name is required').max(255),
  sample_description: z.string().max(255),
  sample_qty: z.number().min(0, 'Must be 0 or more'),
  is_active: z.boolean(),
});
type FormData = z.infer<typeof schema>;
const EMPTY: FormData = { test_name: '', sample_description: '', sample_qty: 0, is_active: true };

interface TestMasterFormProps {
  visible: boolean;
  test: TestMaster | null;
  productId: number;
  saving?: boolean;
  onHide: () => void;
  onSubmit: (data: CreateTestMasterRequest) => void;
}

export const TestMasterForm = ({ visible, test, productId, saving, onHide, onSubmit }: TestMasterFormProps) => {
  const isEdit = Boolean(test);
  const { register, handleSubmit, control, reset, formState: { errors } } = useForm<FormData>({
    resolver: zodResolver(schema), defaultValues: EMPTY,
  });

  useEffect(() => {
    if (!visible) return;
    reset(test
      ? { test_name: test.test_name, sample_description: test.sample_description, sample_qty: test.sample_qty, is_active: test.is_active }
      : EMPTY
    );
  }, [visible, test, reset]);

  const close = () => { reset(EMPTY); onHide(); };

  return (
    <Dialog header={isEdit ? `Edit Test — ${test?.test_name}` : 'New Test'} visible={visible} onHide={close}
      style={{ width: '460px' }} modal aria-label="Test Master dialog"
      footer={
        <div className="flex justify-content-end gap-2">
          <Button label="Cancel" icon="pi pi-times" severity="secondary" outlined onClick={close} type="button" />
          <Button label={isEdit ? 'Save Changes' : 'Create'} icon="pi pi-check" loading={saving} type="button"
            onClick={handleSubmit((d) => onSubmit({
              test_name: d.test_name.trim(),
              sample_description: d.sample_description.trim(),
              sample_qty: d.sample_qty,
              product_id: productId,
              is_active: d.is_active,
            }))} />
        </div>
      }
    >
      <form className="flex flex-column gap-3 pt-3">
        <div className="flex flex-column gap-2">
          <label htmlFor="test-name" className="font-medium text-sm">Test Name <span className="p-error">*</span></label>
          <InputText id="test-name" {...register('test_name')} placeholder="Enter test name"
            className={errors.test_name ? 'p-invalid' : ''} />
          {errors.test_name && <small className="p-error">{errors.test_name.message}</small>}
        </div>
        <div className="flex flex-column gap-2">
          <label htmlFor="test-desc" className="font-medium text-sm">Sample Description</label>
          <InputText id="test-desc" {...register('sample_description')} placeholder="Enter sample description" />
        </div>
        <div className="flex flex-column gap-2">
          <label htmlFor="test-qty" className="font-medium text-sm">Sample Qty</label>
          <Controller name="sample_qty" control={control} render={({ field }) => (
            <InputNumber id="test-qty" value={field.value} onValueChange={(e) => field.onChange(e.value ?? 0)}
              min={0} className="w-full" />
          )} />
        </div>
        <div className="flex align-items-center gap-3">
          <Controller name="is_active" control={control} render={({ field }) => (
            <InputSwitch id="test-active" checked={field.value} onChange={(e) => field.onChange(e.value)} aria-label="Active" />
          )} />
          <label htmlFor="test-active" className="font-medium text-sm cursor-pointer">Active</label>
        </div>
      </form>
    </Dialog>
  );
};
