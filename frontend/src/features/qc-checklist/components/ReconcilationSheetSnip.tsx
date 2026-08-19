/**
 * ReconcilationSheetSnip — grid component for ReconcilationSheet format type checklist.
 *
 * Two grids:
 * 1. Basic Details grid (visible when stage is Basic Details):
 *    Sr No | Questions | Select Options | Enter Answer
 *    - Dropdown for answer_type = Master (ProductMaster) → shows all products
 *    - DateTimePicker for answer_type = DateAndTime
 *    - Standard text/dropdown handling for other answer types
 *
 * 2. Sample Details grid (visible for non-Basic-Details stages):
 *    Sr No | Tests | Sample Vails | Issued By Dates | Received By Dates
 *    - Populates from question answers linked to the stage
 */

import { forwardRef, useEffect, useImperativeHandle, useState } from 'react';
import { InputText } from 'primereact/inputtext';
import { Dropdown } from 'primereact/dropdown';
import { Calendar } from 'primereact/calendar';
import { OptionSelector } from './OptionSelector';
import { apiClient } from '@shared/services/apiClient';

interface QuestionAnswerPreview {
  stage_question_mapping_id: number;
  question_id: number;
  question_title: string;
  serial_number: number;
  section_id: number | null;
  section_name: string | null;
  show_on_grid: boolean;
  answer_type: string;
  has_text_box: boolean;
  has_multiple_text_box: boolean;
  has_sub_question: boolean;
  is_declaration_question: boolean;
  aql_limit: string;
  sub_questions: QuestionAnswerPreview[];
  options: { id: number; label: string }[];
  response_options: { id: number; label: string }[];
}

interface SectionPreview {
  section_id: number;
  section_name: string;
  questions: QuestionAnswerPreview[];
}

interface Props {
  questions: QuestionAnswerPreview[];
  sections: SectionPreview[];
  stageName: string;
  stageStatus: string;
  hasSection: boolean;
}

interface ProductOption {
  id: number;
  product_name: string;
}

export interface ReconcilationSheetSnipHandle {
  validate: () => boolean;
  getAnswers: () => Array<{
    stage_question_mapping_id: number;
    question_id: number;
    textbox_value: string;
    question_option_id: number | null;
    product_id: number | null;
    date_time: string | null;
    response_answer: string;
    helpers: string[];
  }>;
}

export const ReconcilationSheetSnip = forwardRef<ReconcilationSheetSnipHandle, Props>(
  ({ questions, sections, stageName, stageStatus, hasSection }, ref) => {
    const isBasicDetails = stageName === 'Basic Details';
    const canEdit = stageStatus === 'Initial' || stageStatus === 'Draft' || stageStatus === 'ReferBack' || stageStatus === 'Saved';

    const [selections, setSelections] = useState<Record<number, any>>({});
    const [answers, setAnswers] = useState<Record<number, string>>({});
    const [productSelections, setProductSelections] = useState<Record<number, number | null>>({});
    const [dateSelections, setDateSelections] = useState<Record<number, Date | null>>({});
    const [helpers, setHelpers] = useState<Record<number, string[]>>({});
    const [errors, setErrors] = useState<Record<number, string>>({});

    // Products list for Master/ProductMaster dropdowns
    const [products, setProducts] = useState<ProductOption[]>([]);

    useEffect(() => {
      const fetchProducts = async () => {
        try {
          const { data } = await apiClient.get('/masters/products', { params: { limit: 500 } });
          setProducts((data.items || []).map((p: any) => ({ id: p.id, product_name: p.product_name })));
        } catch {
          setProducts([]);
        }
      };
      fetchProducts();
    }, []);

    useImperativeHandle(ref, () => ({
      validate: () => {
        const newErrors: Record<number, string> = {};
        let isValid = true;

        const allQuestions = isBasicDetails
          ? questions
          : hasSection
            ? sections.flatMap((s) => s.questions)
            : questions;

        for (const row of allQuestions) {
          const key = row.stage_question_mapping_id;

          // Dropdown validation
          if (row.answer_type === 'Dropdown (single select)' && !selections[key]) {
            newErrors[key] = 'Choose one option above!';
            isValid = false;
          } else if (row.answer_type === 'Dropdown (multi select)') {
            if (!selections[key] || (Array.isArray(selections[key]) && selections[key].length === 0)) {
              newErrors[key] = 'Choose one/multiple option(s) above!';
              isValid = false;
            }
          }

          // Master/ProductMaster validation
          if (row.answer_type === 'Master' && !productSelections[key]) {
            newErrors[key] = 'Please select a Product!';
            isValid = false;
          }

          // Text box validation
          if (row.answer_type === 'Text Box' || (row.answer_type !== 'None' && row.answer_type !== 'Master' && row.answer_type !== 'DateAndTime' && row.has_text_box)) {
            if (!answers[key] || !answers[key].trim()) {
              newErrors[key] = 'Please enter the value.';
              isValid = false;
            }
          }

          // DateAndTime validation
          if (row.answer_type === 'DateAndTime' && !dateSelections[key]) {
            newErrors[key] = 'Please select a date!';
            isValid = false;
          }
        }

        setErrors(newErrors);
        return isValid;
      },
      getAnswers: () => {
        const allQuestions = isBasicDetails
          ? questions
          : hasSection
            ? sections.flatMap((s) => s.questions)
            : questions;

        return allQuestions.map((row) => {
          const key = row.stage_question_mapping_id;
          return {
            stage_question_mapping_id: key,
            question_id: row.question_id,
            textbox_value: answers[key] || '',
            question_option_id: typeof selections[key] === 'number' ? selections[key] : null,
            product_id: productSelections[key] || null,
            date_time: dateSelections[key] ? dateSelections[key]!.toISOString() : null,
            response_answer: '',
            helpers: helpers[key] || [],
          };
        });
      },
    }));

    // ─── Grid 1: Basic Details ───
    if (isBasicDetails) {
      return (
        <div style={{ overflow: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.78rem' }}>
            <thead>
              <tr style={{ background: '#f8fafc' }}>
                <th style={thStyle('3.5rem', 'center')}>Sr No</th>
                <th style={thStyle(undefined, 'left')}>Questions</th>
                <th style={thStyle('20rem', 'left')}>Select Options</th>
                <th style={thStyle('16rem', 'left')}>Enter Answer</th>
              </tr>
            </thead>
            <tbody>
              {questions.map((row) => {
                const key = row.stage_question_mapping_id;
                const rowErr = errors[key];

                return (
                  <tr key={key} style={{ borderBottom: '1px solid #f1f5f9' }}>
                    <td style={tdCenter}>{row.serial_number}</td>
                    <td style={tdLeft}>{row.question_title}</td>

                    {/* Select Options column */}
                    <td style={tdLeft}>
                      {row.answer_type === 'Master' ? (
                        <Dropdown
                          value={productSelections[key] || null}
                          options={products.map((p) => ({ label: p.product_name, value: p.id }))}
                          onChange={(e) => {
                            setProductSelections((prev) => ({ ...prev, [key]: e.value }));
                            setErrors((prev) => { const c = { ...prev }; delete c[key]; return c; });
                          }}
                          placeholder="Select Product"
                          filter
                          showClear
                          className="w-full"
                          disabled={!canEdit}
                          style={{ height: '1.85rem', fontSize: '0.75rem' }}
                        />
                      ) : (
                        <OptionSelector
                          answerType={row.answer_type}
                          options={row.options}
                          value={selections[key]}
                          onChange={(val) => {
                            setSelections((prev) => ({ ...prev, [key]: val }));
                            setErrors((prev) => { const c = { ...prev }; delete c[key]; return c; });
                          }}
                        />
                      )}
                      {rowErr && row.answer_type !== 'Text Box' && row.answer_type !== 'DateAndTime' && (
                        <small className="qc-validation-error">{rowErr}</small>
                      )}
                    </td>

                    {/* Enter Answer column */}
                    <td style={tdLeft}>
                      {row.answer_type === 'DateAndTime' ? (
                        <div className="flex flex-column gap-1">
                          <Calendar
                            value={dateSelections[key] || null}
                            onChange={(e) => {
                              setDateSelections((prev) => ({ ...prev, [key]: e.value as Date }));
                              setErrors((prev) => { const c = { ...prev }; delete c[key]; return c; });
                            }}
                            showTime
                            hourFormat="12"
                            placeholder="Select Date & Time"
                            disabled={!canEdit}
                            className="w-full"
                            inputStyle={{ height: '1.85rem', fontSize: '0.75rem' }}
                          />
                          {rowErr && (
                            <small className="qc-validation-error">{rowErr}</small>
                          )}
                        </div>
                      ) : row.answer_type === 'Master' || row.answer_type === 'None' || (!row.has_text_box && row.answer_type !== 'Text Box') ? (
                        <span style={{ color: '#94a3b8', fontSize: '0.78rem' }}>N/A</span>
                      ) : (
                        <div className="flex flex-column gap-1">
                          <InputText
                            value={answers[key] || ''}
                            className={rowErr ? 'w-full p-invalid' : 'w-full'}
                            onChange={(e) => {
                              setAnswers((prev) => ({ ...prev, [key]: e.target.value }));
                              setErrors((prev) => { const c = { ...prev }; delete c[key]; return c; });
                            }}
                            disabled={!canEdit}
                            style={{ height: '1.85rem', fontSize: '0.75rem' }}
                          />
                          {rowErr && (
                            <small className="qc-validation-error">{rowErr}</small>
                          )}
                          {/* Helper text boxes */}
                          {(helpers[key] || []).map((val, idx) => (
                            <div key={idx} className="flex align-items-center gap-1">
                              <InputText
                                value={val}
                                className="flex-1"
                                onChange={(e) => setHelpers((prev) => {
                                  const arr = [...(prev[key] || [])];
                                  arr[idx] = e.target.value;
                                  return { ...prev, [key]: arr };
                                })}
                                disabled={!canEdit}
                                style={{ height: '1.85rem', fontSize: '0.75rem' }}
                              />
                              {canEdit && (
                                <button type="button"
                                  onClick={() => setHelpers((prev) => {
                                    const arr = [...(prev[key] || [])];
                                    arr.splice(idx, 1);
                                    return { ...prev, [key]: arr };
                                  })}
                                  style={{ border: 'none', background: 'transparent', color: 'var(--color-error)', cursor: 'pointer' }}>
                                  <i className="pi pi-times" style={{ fontSize: '0.7rem' }} />
                                </button>
                              )}
                            </div>
                          ))}
                          {row.has_multiple_text_box && canEdit && (
                            <button type="button"
                              onClick={() => setHelpers((prev) => ({ ...prev, [key]: [...(prev[key] || []), ''] }))}
                              style={addBtnStyle}>
                              + Add
                            </button>
                          )}
                        </div>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      );
    }

    // ─── Grid 2: Sample Details (non-Basic-Details stages) ───
    // Columns: Sr No | Tests | Sample Vails | Issued By Dates | Received By Dates
    const stageQuestions = hasSection ? sections.flatMap((s) => s.questions) : questions;

    return (
      <div style={{ overflow: 'auto' }}>
        {hasSection && sections.map((section) => (
          <div key={section.section_id}>
            <div style={{
              padding: '0.5rem 0.75rem', fontWeight: 700, fontSize: '0.8rem',
              color: 'var(--color-primary)', background: '#fef2f2', borderBottom: '1px solid #fecaca',
            }}>
              {section.section_name}
            </div>
            <SampleDetailsGrid
              questions={section.questions}
              answers={answers}
              setAnswers={setAnswers}
              dateSelections={dateSelections}
              setDateSelections={setDateSelections}
              canEdit={canEdit}
              errors={errors}
              setErrors={setErrors}
            />
          </div>
        ))}
        {!hasSection && (
          <SampleDetailsGrid
            questions={questions}
            answers={answers}
            setAnswers={setAnswers}
            dateSelections={dateSelections}
            setDateSelections={setDateSelections}
            canEdit={canEdit}
            errors={errors}
            setErrors={setErrors}
          />
        )}
      </div>
    );
  }
);

ReconcilationSheetSnip.displayName = 'ReconcilationSheetSnip';

// ─── Sample Details Grid (Grid 2) ───

interface SampleDetailsGridProps {
  questions: QuestionAnswerPreview[];
  answers: Record<number, string>;
  setAnswers: React.Dispatch<React.SetStateAction<Record<number, string>>>;
  dateSelections: Record<number, Date | null>;
  setDateSelections: React.Dispatch<React.SetStateAction<Record<number, Date | null>>>;
  canEdit: boolean;
  errors: Record<number, string>;
  setErrors: React.Dispatch<React.SetStateAction<Record<number, string>>>;
}

const SampleDetailsGrid = ({
  questions, answers, setAnswers, dateSelections, setDateSelections, canEdit, errors, setErrors,
}: SampleDetailsGridProps) => (
  <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.78rem' }}>
    <thead>
      <tr style={{ background: '#f8fafc' }}>
        <th style={thStyle('3.5rem', 'center')}>Sr No</th>
        <th style={thStyle(undefined, 'left')}>Tests</th>
        <th style={thStyle('8rem', 'center')}>Sample Vails</th>
        <th style={thStyle('12rem', 'center')}>Issued By Dates</th>
        <th style={thStyle('12rem', 'center')}>Received By Dates</th>
      </tr>
    </thead>
    <tbody>
      {questions.map((row) => {
        const key = row.stage_question_mapping_id;
        return (
          <tr key={key} style={{ borderBottom: '1px solid #f1f5f9' }}>
            <td style={tdCenter}>{row.serial_number}</td>
            <td style={tdLeft}>{row.question_title}</td>
            <td style={{ padding: '0.5rem 0.75rem', textAlign: 'center' }}>
              <InputText
                value={answers[`${key}_vails`] || ''}
                className="w-full"
                onChange={(e) => setAnswers((p) => ({ ...p, [`${key}_vails`]: e.target.value }))}
                disabled={!canEdit}
                style={{ height: '1.85rem', fontSize: '0.75rem', textAlign: 'center' }}
              />
            </td>
            <td style={{ padding: '0.5rem 0.75rem', textAlign: 'center' }}>
              <Calendar
                value={dateSelections[`${key}_issued` as any] || null}
                onChange={(e) => {
                  setDateSelections((p) => ({ ...p, [`${key}_issued`]: e.value as Date }));
                  setErrors((p) => { const c = { ...p }; delete c[key]; return c; });
                }}
                showTime
                hourFormat="12"
                placeholder="Select Date"
                disabled={!canEdit}
                className="w-full"
                inputStyle={{ height: '1.85rem', fontSize: '0.75rem' }}
              />
            </td>
            <td style={{ padding: '0.5rem 0.75rem', textAlign: 'center' }}>
              <Calendar
                value={dateSelections[`${key}_received` as any] || null}
                onChange={(e) => {
                  setDateSelections((p) => ({ ...p, [`${key}_received`]: e.value as Date }));
                }}
                showTime
                hourFormat="12"
                placeholder="Select Date"
                disabled={!canEdit}
                className="w-full"
                inputStyle={{ height: '1.85rem', fontSize: '0.75rem' }}
              />
            </td>
          </tr>
        );
      })}
    </tbody>
  </table>
);

// ─── Shared styles ───

const thStyle = (width?: string, align?: string): React.CSSProperties => ({
  padding: '0.5rem 0.75rem',
  textAlign: (align as any) || 'left',
  fontWeight: 700,
  color: '#475569',
  borderBottom: '1px solid #e2e8f0',
  ...(width ? { width } : {}),
});

const tdCenter: React.CSSProperties = { padding: '0.5rem 0.75rem', textAlign: 'center', fontWeight: 500 };
const tdLeft: React.CSSProperties = { padding: '0.5rem 0.75rem', color: '#1e293b' };

const addBtnStyle: React.CSSProperties = {
  border: '1px solid var(--color-primary)',
  borderRadius: '4px',
  background: 'transparent',
  color: 'var(--color-primary)',
  fontSize: '0.7rem',
  padding: '0.2rem 0.5rem',
  cursor: 'pointer',
  width: 'fit-content',
};
