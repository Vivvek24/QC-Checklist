/**
 * Create / edit side panel for a Question.
 * Slides in from the right as a Sidebar panel.
 */

import { useCallback, useEffect, useState } from 'react';
import { zodResolver } from '@hookform/resolvers/zod';
import { Button } from 'primereact/button';
import { Sidebar } from 'primereact/sidebar';
import { Dropdown } from 'primereact/dropdown';
import { InputSwitch } from 'primereact/inputswitch';
import { InputTextarea } from 'primereact/inputtextarea';
import { Controller, useForm } from 'react-hook-form';
import { z } from 'zod';
import { ANSWER_TYPE_OPTIONS } from '../models/Question';
import { useValidationTypes } from '../hooks/useValidationTypes';
import { useQuestions } from '../hooks/useQuestions';
import { questionOptionApi } from '../api/questionOptionApi';
import { QuestionFormOptions } from './QuestionFormOptions';
import { QuestionFormResponseOptions } from './QuestionFormResponseOptions';
import { QuestionFormSubQuestions } from './QuestionFormSubQuestions';
import type { QuestionOptionFormData } from './QuestionOptionForm';
import type { LocalOptionWithTemp } from './QuestionFormOptions';
import type { CreateQuestionRequest, Question } from '../models/Question';
import type { QuestionOption } from '../models/QuestionOption';

const BOOL_FLAGS = [
  { name: 'has_text_box',          label: 'Has Text Box' },
  { name: 'has_multiple_text_box', label: 'Has Multiple Text Box' },
  { name: 'has_sub_question',      label: 'Has Sub Question' },
  { name: 'is_validation_required',label: 'Validation Required' },
  { name: 'has_response_option',   label: 'Has Response Option' },
  { name: 'has_associated_master', label: 'Has Associated Master' },
  { name: 'is_calculated',         label: 'Is Calculated' },
  { name: 'is_active',             label: 'Active' },
] as const;

type FlagName = (typeof BOOL_FLAGS)[number]['name'];

const MASTER_TYPE_OPTIONS = [
  { label: 'Product Master', value: 'Product Master' },
];

const schema = z.object({
  title: z.string().min(1, 'Title is required').max(500),
  answer_type: z.string().min(1, 'Answer Type is required'),
  has_text_box: z.boolean(),
  has_multiple_text_box: z.boolean(),
  has_sub_question: z.boolean(),
  is_validation_required: z.boolean(),
  has_response_option: z.boolean(),
  allow_multiple_input: z.boolean(),
  has_associated_master: z.boolean(),
  is_calculated: z.boolean(),
  is_active: z.boolean(),
  validation_type_id: z.number().nullable(),
  master_type: z.string().nullable(),
  parent_question_id: z.number().nullable(),
  sub_question_ids: z.array(z.number()),
});

type FormData = z.infer<typeof schema>;

const EMPTY: FormData = {
  title: '', answer_type: '',
  has_text_box: false, has_multiple_text_box: false, has_sub_question: false,
  is_validation_required: false, has_response_option: false, allow_multiple_input: false,
  has_associated_master: false, is_calculated: false, is_active: true,
  validation_type_id: null, master_type: null, parent_question_id: null,
  sub_question_ids: [],
};

export interface LocalOption {
  id?: number;
  option_title: string;
  is_active: boolean;
  is_response_option?: boolean;
}

interface QuestionFormProps {
  visible: boolean;
  question: Question | null;
  saving?: boolean;
  onHide: () => void;
  onSubmit: (data: CreateQuestionRequest & { options: LocalOption[] }) => void;
}

let optCounter = 0;

export const QuestionForm = ({ visible, question, saving, onHide, onSubmit }: QuestionFormProps) => {
  const isEdit = Boolean(question);
  const questionId = question ? Number(question.id) : undefined;
  const { handleSubmit, control, reset, watch, setValue, formState: { errors } } = useForm<FormData>({
    resolver: zodResolver(schema), defaultValues: EMPTY,
  });
  const { data: vtData } = useValidationTypes();
  const vtOptions = (vtData?.items ?? []).map((vt) => ({ label: vt.name, value: Number(vt.id) }));
  const { data: questionsData } = useQuestions();
  const questionOptions = (questionsData?.items ?? [])
    .map((q) => ({ label: q.title, value: Number(q.id) }));

  const answerType = watch('answer_type');
  const hasTextBox = watch('has_text_box');
  const hasResponseOption = watch('has_response_option');
  const isValidationRequired = watch('is_validation_required');
  const hasSubQuestion = watch('has_sub_question');

  // Local options state
  const [localOptions, setLocalOptions] = useState<LocalOptionWithTemp[]>([]);
  const [optionFormVisible, setOptionFormVisible] = useState(false);
  const [editingOptIdx, setEditingOptIdx] = useState<number | null>(null);

  // Local response options state (is_response_option = true)
  const [localRespOptions, setLocalRespOptions] = useState<LocalOptionWithTemp[]>([]);
  const [respOptFormVisible, setRespOptFormVisible] = useState(false);
  const [editingRespOptIdx, setEditingRespOptIdx] = useState<number | null>(null);

  const loadOptions = useCallback(async (qId: number) => {
    try {
      const result = await questionOptionApi.list({ question_id: qId });
      const regular: LocalOptionWithTemp[] = [];
      const response: LocalOptionWithTemp[] = [];
      for (const o of result.items) {
        const item: LocalOptionWithTemp = { tempId: `ex-${o.id}`, id: Number(o.id), option_title: o.option_title, is_active: o.is_active };
        if (o.is_response_option) { response.push(item); } else { regular.push(item); }
      }
      setLocalOptions(regular);
      setLocalRespOptions(response);
    } catch { setLocalOptions([]); setLocalRespOptions([]); }
  }, []);

  useEffect(() => {
    if (!visible) return;
    reset(question ? {
      title: question.title, answer_type: question.answer_type,
      has_text_box: question.has_text_box, has_multiple_text_box: question.has_multiple_text_box,
      has_sub_question: question.has_sub_question,
      is_validation_required: question.is_validation_required,
      has_response_option: question.has_response_option,
      allow_multiple_input: question.allow_multiple_input,
      has_associated_master: question.has_associated_master,
      is_calculated: question.is_calculated, is_active: question.is_active,
      validation_type_id: question.validation_type_id ?? null,
      master_type: question.master_type ?? null,
      parent_question_id: question.parent_question_id ?? null,
      sub_question_ids: question.sub_question_ids ?? [],
    } : EMPTY);
    setOptionFormVisible(false);
    setEditingOptIdx(null);
    setRespOptFormVisible(false);
    setEditingRespOptIdx(null);
    if (questionId) { loadOptions(questionId); } else { setLocalOptions([]); setLocalRespOptions([]); }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [visible]);

  const close = () => { reset(EMPTY); setLocalOptions([]); setLocalRespOptions([]); onHide(); };

  // Option handlers
  const openAddOption = () => { setEditingOptIdx(null); setOptionFormVisible(true); };
  const openEditOption = (idx: number) => { setEditingOptIdx(idx); setOptionFormVisible(true); };
  const deleteOption = (idx: number) => setLocalOptions((prev) => prev.filter((_, i) => i !== idx));

  const handleOptionSave = (data: QuestionOptionFormData) => {
    if (editingOptIdx !== null) {
      setLocalOptions((prev) => prev.map((o, i) => i === editingOptIdx ? { ...o, ...data } : o));
    } else {
      setLocalOptions((prev) => [...prev, { tempId: `new-${++optCounter}`, ...data }]);
    }
    setOptionFormVisible(false);
    setEditingOptIdx(null);
  };

  // Response option handlers
  const openAddRespOption = () => { setEditingRespOptIdx(null); setRespOptFormVisible(true); };
  const openEditRespOption = (idx: number) => { setEditingRespOptIdx(idx); setRespOptFormVisible(true); };
  const deleteRespOption = (idx: number) => setLocalRespOptions((prev) => prev.filter((_, i) => i !== idx));

  const handleRespOptionSave = (data: QuestionOptionFormData) => {
    if (editingRespOptIdx !== null) {
      setLocalRespOptions((prev) => prev.map((o, i) => i === editingRespOptIdx ? { ...o, ...data } : o));
    } else {
      setLocalRespOptions((prev) => [...prev, { tempId: `new-${++optCounter}`, ...data }]);
    }
    setRespOptFormVisible(false);
    setEditingRespOptIdx(null);
  };

  const submit = (data: FormData) => {
    onSubmit({
      title: data.title,
      answer_type: data.answer_type as CreateQuestionRequest['answer_type'],
      has_text_box: data.has_text_box,
      has_multiple_text_box: data.has_multiple_text_box,
      has_sub_question: data.has_sub_question,
      is_validation_required: data.is_validation_required,
      has_response_option: data.has_response_option,
      allow_multiple_input: data.allow_multiple_input,
      has_associated_master: data.has_associated_master,
      is_calculated: data.is_calculated,
      is_active: data.is_active,
      validation_type_id: data.validation_type_id,
      master_type: data.master_type,
      parent_question_id: data.parent_question_id,
      sub_question_ids: data.sub_question_ids,
      options: [
        ...localOptions.map((o) => ({ id: o.id, option_title: o.option_title, is_active: o.is_active, is_response_option: false })),
        ...localRespOptions.map((o) => ({ id: o.id, option_title: o.option_title, is_active: o.is_active, is_response_option: true })),
      ],
    });
  };

  const editingOption: QuestionOption | null = editingOptIdx !== null && localOptions[editingOptIdx]
    ? { ...localOptions[editingOptIdx], id: String(localOptions[editingOptIdx].id ?? ''), created_by: '', created_date: '', modified_by: '', modified_date: '', question_id: 0, is_response_option: false } as QuestionOption
    : null;

  const editingRespOption: QuestionOption | null = editingRespOptIdx !== null && localRespOptions[editingRespOptIdx]
    ? { ...localRespOptions[editingRespOptIdx], id: String(localRespOptions[editingRespOptIdx].id ?? ''), created_by: '', created_date: '', modified_by: '', modified_date: '', question_id: 0, is_response_option: true } as QuestionOption
    : null;

  const headerContent = (
    <div className="flex align-items-center gap-2">
      <i className="pi pi-question-circle" style={{ fontSize: '1.2rem', color: 'var(--color-primary)' }} />
      <span className="font-semibold" style={{ fontSize: '1rem' }}>
        {isEdit ? `Edit Question` : 'New Question'}
      </span>
    </div>
  );

  return (
    <Sidebar
      visible={visible}
      onHide={close}
      position="right"
      className="em-sidebar-panel"
      header={headerContent}
    >
      <form className="flex flex-column gap-3" onSubmit={(e) => e.preventDefault()}>
        {/* Title */}
        <div className="flex flex-column gap-2">
          <label htmlFor="q-title" className="font-medium text-sm">Title <span className="p-error">*</span></label>
          <Controller name="title" control={control} render={({ field }) => (
            <InputTextarea id="q-title" value={field.value} onChange={(e) => field.onChange(e.target.value)}
              placeholder="Enter question title" rows={3} autoResize
              className={errors.title ? 'p-invalid w-full' : 'w-full'} />
          )} />
          {errors.title && <small className="p-error">{errors.title.message}</small>}
        </div>

        {/* Dropdowns — 2 by 2 */}
        <div className="grid">
          <div className="col-6 flex flex-column gap-2">
            <label htmlFor="q-answer-type" className="font-medium text-sm">Answer Type <span className="p-error">*</span></label>
            <Controller name="answer_type" control={control} render={({ field }) => (
              <Dropdown id="q-answer-type" value={field.value || null} options={ANSWER_TYPE_OPTIONS}
                onChange={(e) => field.onChange(e.value)} placeholder="Select Answer Type"
                className={errors.answer_type ? 'p-invalid w-full' : 'w-full'} />
            )} />
            {errors.answer_type && <small className="p-error">{errors.answer_type.message}</small>}
          </div>
          <div className="col-6 flex flex-column gap-2">
            <label htmlFor="q-validation-type" className="font-medium text-sm">Validation Type</label>
            <Controller name="validation_type_id" control={control} render={({ field }) => (
              <Dropdown id="q-validation-type" value={field.value} options={vtOptions}
                onChange={(e) => field.onChange(e.value)} placeholder="Select Validation Type"
                showClear className="w-full" />
            )} />
          </div>
        </div>

        {/* Question Mapping — visible when is_validation_required is ON */}
        {isValidationRequired && (
          <div className="flex flex-column gap-2">
            <label htmlFor="q-parent-question" className="font-medium text-sm">Question Mapping</label>
            <Controller name="parent_question_id" control={control} render={({ field }) => (
              <Dropdown id="q-parent-question" value={field.value} options={questionOptions}
                onChange={(e) => field.onChange(e.value)} placeholder="Select Question"
                filter showClear className="w-full" />
            )} />
          </div>
        )}

        {/* Sub Questions — visible when has_sub_question is ON */}
        {hasSubQuestion && (
          <Controller name="sub_question_ids" control={control} render={({ field }) => (
            <QuestionFormSubQuestions
              value={field.value}
              questionOptions={questionOptions}
              onChange={(ids) => { field.onChange(ids); setValue('sub_question_ids', ids); }}
            />
          )} />
        )}

        {/* Master Type — only visible when answer_type is 'Masters' */}
        {answerType === 'Masters' && (
          <div className="flex flex-column gap-2">
            <label htmlFor="q-master-type" className="font-medium text-sm">Master Type</label>
            <Controller name="master_type" control={control} render={({ field }) => (
              <Dropdown id="q-master-type" value={field.value} options={MASTER_TYPE_OPTIONS}
                onChange={(e) => field.onChange(e.value)} placeholder="Select Master Type"
                showClear className="w-full" />
            )} />
          </div>
        )}

        {/* Boolean flags — 2-column grid */}
        <div className="grid mt-2">
          {BOOL_FLAGS.map(({ name, label }) => (
            <div key={name} className="col-6 flex align-items-center gap-2 py-1">
              <Controller name={name as FlagName} control={control} render={({ field }) => (
                <InputSwitch id={`q-${name}`} checked={field.value} onChange={(e) => field.onChange(e.value)}
                  aria-label={label} />
              )} />
              <label htmlFor={`q-${name}`} className="font-medium text-sm cursor-pointer">{label}</label>
            </div>
          ))}
          {/* Allow Multiple Input — only visible when has_text_box is true */}
          {hasTextBox && (
            <div className="col-6 flex align-items-center gap-2 py-1">
              <Controller name="allow_multiple_input" control={control} render={({ field }) => (
                <InputSwitch id="q-allow_multiple_input" checked={field.value} onChange={(e) => field.onChange(e.value)}
                  aria-label="Allow Multiple Input" />
              )} />
              <label htmlFor="q-allow_multiple_input" className="font-medium text-sm cursor-pointer">Allow Multiple Input</label>
            </div>
          )}
        </div>

        {/* Add Options — visible when answer_type is dropdown single/multi */}
        {(answerType === 'Dropdown (single select)' || answerType === 'Dropdown (multi select)') && (
          <QuestionFormOptions
            localOptions={localOptions}
            optionFormVisible={optionFormVisible}
            editingOption={editingOption}
            onAddOption={openAddOption}
            onEditOption={openEditOption}
            onDeleteOption={deleteOption}
            onOptionFormHide={() => { setOptionFormVisible(false); setEditingOptIdx(null); }}
            onOptionFormSave={handleOptionSave}
          />
        )}

        {/* Add Response Options — visible when has_response_option is true */}
        {hasResponseOption && (
          <QuestionFormResponseOptions
            localRespOptions={localRespOptions}
            respOptFormVisible={respOptFormVisible}
            editingRespOption={editingRespOption}
            onAddRespOption={openAddRespOption}
            onEditRespOption={openEditRespOption}
            onDeleteRespOption={deleteRespOption}
            onRespOptFormHide={() => { setRespOptFormVisible(false); setEditingRespOptIdx(null); }}
            onRespOptFormSave={handleRespOptionSave}
          />
        )}

        {/* Footer actions */}
        <div className="flex justify-content-end gap-2 mt-3 pt-3" style={{ borderTop: '1px solid var(--color-surface-border)' }}>
          <Button label="Cancel" icon="pi pi-times" severity="secondary" outlined onClick={close} type="button" />
          <Button label={isEdit ? 'Save Changes' : 'Create'} icon="pi pi-check" loading={saving}
            onClick={handleSubmit(submit)} type="button" />
        </div>
      </form>
    </Sidebar>
  );
};
