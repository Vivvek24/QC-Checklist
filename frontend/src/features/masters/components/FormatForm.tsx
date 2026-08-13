/**
 * Create / edit dialog for a Format.
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
import { useUnits } from '../hooks/useUnits';
import { FORMAT_TYPE_OPTIONS } from '../models/Format';
import type { CreateFormatRequest, Format } from '../models/Format';

const schema = z.object({
  format_no: z.string().min(1, 'Format No is required').max(100),
  format_title: z.string().min(1, 'Format Title is required').max(255),
  format_name: z.string().min(1, 'Format Name is required').max(255),
  unit_id: z.number({ required_error: 'Unit is required' }).min(1, 'Unit is required'),
  format_type: z.string().min(1, 'Format Type is required'),
  has_declaration_question: z.boolean(),
  is_active: z.boolean(),
});

type FormData = z.infer<typeof schema>;

const EMPTY: FormData = {
  format_no: '', format_title: '', format_name: '',
  unit_id: 0, format_type: '', has_declaration_question: false, is_active: true,
};

interface FormatFormProps {
  visible: boolean;
  format: Format | null;
  saving?: boolean;
  onHide: () => void;
  onSubmit: (data: CreateFormatRequest) => void;
}

export const FormatForm = ({ visible, format, saving, onHide, onSubmit }: FormatFormProps) => {
  const isEdit = Boolean(format);
  const { data: unitData } = useUnits({ is_active: true });
  const unitOptions = (unitData?.items ?? []).map((u) => ({ label: u.name, value: u.id }));

  const { register, handleSubmit, control, reset, formState: { errors } } = useForm<FormData>({
    resolver: zodResolver(schema), defaultValues: EMPTY,
  });

  useEffect(() => {
    if (!visible) return;
    reset(format
      ? { format_no: format.format_no, format_title: format.format_title, format_name: format.format_name,
          unit_id: format.unit_id, format_type: format.format_type, has_declaration_question: format.has_declaration_question, is_active: format.is_active }
      : EMPTY
    );
  }, [visible, format, reset]);

  const close = () => { reset(EMPTY); onHide(); };

  const submit = (data: FormData) => {
    onSubmit({
      format_no: data.format_no.trim(),
      format_title: data.format_title.trim(),
      format_name: data.format_name.trim(),
      unit_id: data.unit_id,
      format_type: data.format_type as any,
      has_declaration_question: data.has_declaration_question,
      is_active: data.is_active,
    });
  };

  return (
    <Dialog
      header={isEdit ? `Edit Format — ${format?.format_no}` : 'New Format'}
      visible={visible} onHide={close} style={{ width: '500px' }} modal
      aria-label="Format dialog"
      footer={
        <div className="flex justify-content-end gap-2">
          <Button label="Cancel" icon="pi pi-times" severity="secondary" outlined onClick={close} />
          <Button label={isEdit ? 'Save Changes' : 'Create'} icon="pi pi-check" loading={saving} onClick={handleSubmit(submit)} />
        </div>
      }
    >
      <form className="flex flex-column gap-3 pt-3">
        <div className="flex flex-column gap-2">
          <label htmlFor="fmt-no" className="font-medium text-sm">Format No <span className="p-error">*</span></label>
          <InputText id="fmt-no" {...register('format_no')} placeholder="e.g. FMT-001" className={errors.format_no ? 'p-invalid' : ''} />
          {errors.format_no && <small className="p-error">{errors.format_no.message}</small>}
        </div>

        <div className="flex flex-column gap-2">
          <label htmlFor="fmt-title" className="font-medium text-sm">Format Title <span className="p-error">*</span></label>
          <InputText id="fmt-title" {...register('format_title')} placeholder="Enter format title" className={errors.format_title ? 'p-invalid' : ''} />
          {errors.format_title && <small className="p-error">{errors.format_title.message}</small>}
        </div>

        <div className="flex flex-column gap-2">
          <label htmlFor="fmt-name" className="font-medium text-sm">Format Name <span className="p-error">*</span></label>
          <InputText id="fmt-name" {...register('format_name')} placeholder="Enter format name" className={errors.format_name ? 'p-invalid' : ''} />
          {errors.format_name && <small className="p-error">{errors.format_name.message}</small>}
        </div>

        <div className="flex flex-column gap-2">
          <label htmlFor="fmt-unit" className="font-medium text-sm">Unit <span className="p-error">*</span></label>
          <Controller name="unit_id" control={control} render={({ field }) => (
            <Dropdown id="fmt-unit" value={field.value || null} options={unitOptions}
              onChange={(e) => field.onChange(e.value)} placeholder="Select Unit" filter
              className={errors.unit_id ? 'p-invalid' : ''} />
          )} />
          {errors.unit_id && <small className="p-error">{errors.unit_id.message}</small>}
        </div>

        <div className="flex flex-column gap-2">
          <label htmlFor="fmt-type" className="font-medium text-sm">Format Type <span className="p-error">*</span></label>
          <Controller name="format_type" control={control} render={({ field }) => (
            <Dropdown id="fmt-type" value={field.value || null} options={FORMAT_TYPE_OPTIONS}
              onChange={(e) => field.onChange(e.value)} placeholder="Select Format Type"
              className={errors.format_type ? 'p-invalid' : ''} />
          )} />
          {errors.format_type && <small className="p-error">{errors.format_type.message}</small>}
        </div>

        <div className="flex align-items-center gap-3">
          <Controller name="has_declaration_question" control={control} render={({ field }) => (
            <InputSwitch id="fmt-decl" checked={field.value} onChange={(e) => field.onChange(e.value)} aria-label="Has Declaration Question" />
          )} />
          <label htmlFor="fmt-decl" className="font-medium text-sm cursor-pointer">Has Declaration Question</label>
        </div>

        <div className="flex align-items-center gap-3">
          <Controller name="is_active" control={control} render={({ field }) => (
            <InputSwitch id="fmt-active" checked={field.value} onChange={(e) => field.onChange(e.value)} aria-label="Active" />
          )} />
          <label htmlFor="fmt-active" className="font-medium text-sm cursor-pointer">Active</label>
        </div>
      </form>
    </Dialog>
  );
};
