/**
 * AddSectionStageQuestionForm — form for adding/editing a question mapping under a section.
 * Fields: Serial Number, Question dropdown, AQL Limit (when format is AQL), Is Declaration Question, Active.
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
import { useQuestions } from '../hooks/useQuestions';
import { FORMAT_TYPE } from '../constants';

const schema = z.object({
  serial_number: z.number().min(0),
  question_id: z.number({ required_error: 'Question is required' }).min(1),
  aql_limit: z.string(),
  is_declaration_question: z.boolean(),
  is_active: z.boolean(),
});
type FD = z.infer<typeof schema>;
const EMPTY: FD = {
  serial_number: 0, question_id: 0, aql_limit: '',
  is_declaration_question: false, is_active: true,
};

export interface SectionStageQuestionFormData {
  serial_number: number;
  question_id: number;
  aql_limit: string;
  is_declaration_question: boolean;
  is_active: boolean;
}

interface Props {
  visible: boolean;
  formatType: string;
  hasDeclarationQuestion: boolean;
  defaultSerialNumber?: number;
  initialData?: Partial<SectionStageQuestionFormData>;
  saving?: boolean;
  onHide: () => void;
  onSubmit: (data: SectionStageQuestionFormData) => void;
}

export const AddSectionStageQuestionForm = ({ visible, formatType, hasDeclarationQuestion, defaultSerialNumber, initialData, saving, onHide, onSubmit }: Props) => {
  const { data: questionsData } = useQuestions();
  const questionOptions = (questionsData?.items ?? []).map((q) => ({ label: q.title, value: Number(q.id) }));

  const { handleSubmit, control, reset, formState: { errors } } = useForm<FD>({
    resolver: zodResolver(schema), defaultValues: EMPTY,
  });

  useEffect(() => { if (visible) reset({ ...EMPTY, serial_number: defaultSerialNumber ?? 0, ...initialData }); }, [visible, reset, defaultSerialNumber, initialData]);

  const close = () => { reset(EMPTY); onHide(); };

  const isAQL = formatType === FORMAT_TYPE.AQL;

  return (
    <Dialog header="Section Question Mapping" visible={visible} onHide={close}
      style={{ width: '480px' }} modal
      footer={
        <div className="flex justify-content-end gap-2">
          <Button label="Cancel" severity="secondary" outlined onClick={close} type="button" />
          <Button label="Save" loading={saving} onClick={handleSubmit((d) => onSubmit(d))} type="button" />
        </div>
      }
    >
      <form className="flex flex-column gap-3 pt-2" onSubmit={(e) => e.preventDefault()}>
        {/* Serial Number */}
        <div className="flex flex-column gap-2">
          <label className="font-medium text-sm">Serial Number</label>
          <Controller name="serial_number" control={control} render={({ field }) => (
            <InputText type="number" min="0" value={String(field.value)}
              onChange={(e) => field.onChange(Math.max(0, Number(e.target.value)))}
              placeholder="0" className="w-full" />
          )} />
        </div>

        {/* Question dropdown */}
        <div className="flex flex-column gap-2">
          <label className="font-medium text-sm">Question <span className="p-error">*</span></label>
          <Controller name="question_id" control={control} render={({ field }) => (
            <Dropdown value={field.value || null} options={questionOptions}
              onChange={(e) => field.onChange(e.value)} placeholder="Select Question"
              filter className={errors.question_id ? 'p-invalid w-full' : 'w-full'} />
          )} />
          {errors.question_id && <small className="p-error">{errors.question_id.message}</small>}
        </div>

        {/* AQL Limit — when format_type = AQL */}
        {isAQL && (
          <div className="flex flex-column gap-2">
            <label className="font-medium text-sm">AQL Limit</label>
            <Controller name="aql_limit" control={control} render={({ field }) => (
              <InputText value={field.value} onChange={(e) => field.onChange(e.target.value)}
                placeholder="e.g. 2.5" className="w-full" />
            )} />
          </div>
        )}

        {/* Declaration Question — when format.has_declaration_question */}
        {hasDeclarationQuestion && (
          <div className="flex align-items-center gap-3">
            <Controller name="is_declaration_question" control={control} render={({ field }) => (
              <InputSwitch checked={field.value} onChange={(e) => field.onChange(e.value)} />
            )} />
            <label className="font-medium text-sm">Declaration Question</label>
          </div>
        )}

        {/* Active */}
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
