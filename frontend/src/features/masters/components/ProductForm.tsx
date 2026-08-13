import { useEffect } from 'react';
import { zodResolver } from '@hookform/resolvers/zod';
import { Button } from 'primereact/button';
import { Dialog } from 'primereact/dialog';
import { InputSwitch } from 'primereact/inputswitch';
import { InputText } from 'primereact/inputtext';
import { InputTextarea } from 'primereact/inputtextarea';
import { Controller, useForm } from 'react-hook-form';
import { z } from 'zod';
import type { Product, CreateProductRequest } from '../models/Product';

const schema = z.object({
  product_name: z.string().min(1, 'Product Name is required').max(255),
  storage_conditions: z.string().max(2000),
  is_active: z.boolean(),
});
type FormData = z.infer<typeof schema>;
const EMPTY: FormData = { product_name: '', storage_conditions: '', is_active: true };

interface ProductFormProps {
  visible: boolean;
  product: Product | null;
  saving?: boolean;
  onHide: () => void;
  onSubmit: (data: CreateProductRequest) => void;
}

export const ProductForm = ({ visible, product, saving, onHide, onSubmit }: ProductFormProps) => {
  const isEdit = Boolean(product);
  const { register, handleSubmit, control, reset, formState: { errors } } = useForm<FormData>({ resolver: zodResolver(schema), defaultValues: EMPTY });

  useEffect(() => {
    if (!visible) return;
    reset(product ? { product_name: product.product_name, storage_conditions: product.storage_conditions, is_active: product.is_active } : EMPTY);
  }, [visible, product, reset]);

  const close = () => { reset(EMPTY); onHide(); };

  return (
    <Dialog header={isEdit ? `Edit Product — ${product?.product_name}` : 'New Product'} visible={visible} onHide={close}
      style={{ width: '460px' }} modal aria-label="Product dialog"
      footer={
        <div className="flex justify-content-end gap-2">
          <Button label="Cancel" icon="pi pi-times" severity="secondary" outlined onClick={close} />
          <Button label={isEdit ? 'Save Changes' : 'Create'} icon="pi pi-check" loading={saving}
            onClick={handleSubmit((d) => onSubmit({ product_name: d.product_name.trim(), storage_conditions: d.storage_conditions.trim(), is_active: d.is_active }))} />
        </div>
      }
    >
      <form className="flex flex-column gap-3 pt-3">
        <div className="flex flex-column gap-2">
          <label htmlFor="prod-name" className="font-medium text-sm">Product Name <span className="p-error">*</span></label>
          <InputText id="prod-name" {...register('product_name')} placeholder="Enter product name" className={errors.product_name ? 'p-invalid' : ''} />
          {errors.product_name && <small className="p-error">{errors.product_name.message}</small>}
        </div>
        <div className="flex flex-column gap-2">
          <label htmlFor="prod-storage" className="font-medium text-sm">Storage Conditions</label>
          <InputTextarea id="prod-storage" {...register('storage_conditions')} placeholder="e.g. Store at 2-8°C" rows={3} autoResize />
        </div>
        <div className="flex align-items-center gap-3">
          <Controller name="is_active" control={control} render={({ field }) => (
            <InputSwitch id="prod-active" checked={field.value} onChange={(e) => field.onChange(e.value)} aria-label="Active" />
          )} />
          <label htmlFor="prod-active" className="font-medium text-sm cursor-pointer">Active</label>
        </div>
      </form>
    </Dialog>
  );
};
