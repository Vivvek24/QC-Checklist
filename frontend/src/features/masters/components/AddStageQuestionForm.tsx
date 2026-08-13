/**
 * Add/Edit Stage Question Mapping form dialog.
 * Conditional fields based on stage name and format type.
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
import { useSapFields } from '../hooks/useSapFields';
import { BASIC_DETAILS_STAGE, FORMAT_TYPE, CUSTOM_ANSWER_OPTIONS } from '../constants';

const schema = z.object({
  serial_number: z.number().min(0),
  question_id: z.number({ required_error: 'Question is required' }).min(1),
  show_on_grid: z.boolean(),
  sap_field_id: z.number().nullable(),
  is_editable: z.boolean(),
  is_declaration_question: z.boolean(),
  custom_answers: z.string().nullable(),
  is_active: z.boolean(),
});
type FD = z.infer<typeof schema>;
const EMPTY: FD = {
  serial_number: 0, question_id: 0, show_on_grid: false,
  sap_field_id: null, is_editable: true, is_declaration_question: false,
  custom_answers: null, is_active: true,
};

export interface AddStageQuestionFormData {
  serial_number: number;
  question_id: number;
  show_on_grid: boolean;
  sap_field_id: number | null;
  is_editable: boolean;
  is_declaration_question: boolean;
  custom_answers: string | null;
  is_active: boolean;
}

interface Props {
  visible: boolean;
  stageName: string;
  formatType: string;
  hasDeclarationQuestion: boolean;
  defaultSerialNumber?: number;
  saving?: boolean;
  onHide: () => void;
  onSubmit: (data: AddStageQuestionFormData) => void;
}

export const AddStageQuestionForm = ({ visible, stageName, formatType, hasDeclarationQuestion, defaultSerialNumber, saving, onHide, onSubmit }: Props) => {
  const { data: questionsData } = useQuestions();
  const { data: sapFieldsData } = useSapFields();

  const questionOptions = (questionsData?.items ?? []).map((q) => ({ label: q.title, value: Number(q.id) }));
  const sapFieldOptions = (sapFieldsData?.items ?? []).map((s) => ({ label: (s as any).field_name ?? (s as any).name, value: Number(s.id) }));

  const { handleSubmit, control, reset, formState: { errors } } = useForm<FD>({
    resolver: zodResolver(schema), defaultValues: EMPTY,
  });

  useEffect(() => { if (visible) reset({ ...EMPTY, serial_number: defaultSerialNumber ?? 0 }); }, [visible, reset, defaultSerialNumber]);

  const close = () => { reset(EMPTY); onHide(); };

  const isBasicDetails = stageName === BASIC_DETAILS_STAGE;
  const isAQL = formatType === FORMAT_TYPE.AQL;
  const isReconcilation = formatType === FORMAT_TYPE.RECONCILATION_SHEET;

  // Visibility rules
  const showShowOnGrid = isBasicDetails;
  const showSapField = isBasicDetails && isAQL;
  const showIsEditable = isBasicDetails && (isAQL || isReconcilation);
  const showDeclaration = hasDeclarationQuestion && !isBasicDetails;
  const showCustomAnswers = isReconcilation;

  return (
    <Dialog header="Add Question Mapping" visible={visible} onHide={close}
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

        {/* Show on Grid — only when stage = Basic Details */}
        {showShowOnGrid && (
          <div className="flex align-items-center gap-3">
            <Controller name="show_on_grid" control={control} render={({ field }) => (
              <InputSwitch checked={field.value} onChange={(e) => field.onChange(e.value)} />
            )} />
            <label className="font-medium text-sm">Show on Grid</label>
          </div>
        )}

        {/* SAP Answer Field — only when stage = Basic Details AND format = AQL */}
        {showSapField && (
          <div className="flex flex-column gap-2">
            <label className="font-medium text-sm">SAP Answer Field</label>
            <Controller name="sap_field_id" control={control} render={({ field }) => (
              <Dropdown value={field.value} options={sapFieldOptions}
                onChange={(e) => field.onChange(e.value)} placeholder="Select SAP Field"
                filter showClear className="w-full" />
            )} />
          </div>
        )}

        {/* Is Editable — when stage = Basic Details AND (AQL or ReconcilationSheet) */}
        {showIsEditable && (
          <div className="flex align-items-center gap-3">
            <Controller name="is_editable" control={control} render={({ field }) => (
              <InputSwitch checked={field.value} onChange={(e) => field.onChange(e.value)} />
            )} />
            <label className="font-medium text-sm">Is Editable</label>
          </div>
        )}

        {/* Declaration Question — when format.has_declaration_question AND stage != Basic Details */}
        {showDeclaration && (
          <div className="flex align-items-center gap-3">
            <Controller name="is_declaration_question" control={control} render={({ field }) => (
              <InputSwitch checked={field.value} onChange={(e) => field.onChange(e.value)} />
            )} />
            <label className="font-medium text-sm">Declaration Question</label>
          </div>
        )}

        {/* Custom Answers — when format_type = ReconcilationSheet */}
        {showCustomAnswers && (
          <div className="flex flex-column gap-2">
            <label className="font-medium text-sm">Custom Answer Type</label>
            <Controller name="custom_answers" control={control} render={({ field }) => (
              <Dropdown value={field.value} options={CUSTOM_ANSWER_OPTIONS}
                onChange={(e) => field.onChange(e.value)} placeholder="Select Custom Answer"
                showClear className="w-full" />
            )} />
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
