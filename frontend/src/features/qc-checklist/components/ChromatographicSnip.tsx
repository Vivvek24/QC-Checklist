/**
 * ChromatographicSnip — grid component for Chromatographic format type checklist.
 * Uses a plain table layout to avoid PrimeReact DataTable re-render issues with controlled inputs.
 * Exposes validate() via ref for parent to trigger inline validation on Submit.
 */

import { forwardRef, useImperativeHandle, useState } from 'react';
import { InputText } from 'primereact/inputtext';
import { RadioButton } from 'primereact/radiobutton';
import { OptionSelector } from './OptionSelector';

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
  options: { id: number; label: string }[];
}

interface Props {
  questions: QuestionAnswerPreview[];
  stageName: string;
  stageStatus: string;
}

export interface ChromatographicSnipHandle {
  validate: () => boolean;
  getAnswers: () => Array<{
    stage_question_mapping_id: number;
    question_id: number;
    textbox_value: string;
    question_option_id: number | null;
    response_answer: string;
    helpers: string[];
  }>;
}

export const ChromatographicSnip = forwardRef<ChromatographicSnipHandle, Props>(({ questions, stageName, stageStatus }, ref) => {
  const isBasicDetails = stageName === 'Basic Details';
  const canAdd = stageStatus === 'Initial' || stageStatus === 'Draft' || stageStatus === 'ReferBack';

  const [selections, setSelections] = useState<Record<number, any>>({});
  const [answers, setAnswers] = useState<Record<number, string>>({});
  const [responses, setResponses] = useState<Record<number, string>>({});
  const [helpers, setHelpers] = useState<Record<number, string[]>>({});
  const [errors, setErrors] = useState<Record<number, { options?: string; answer?: string; response?: string }>>({});

  useImperativeHandle(ref, () => ({
    validate: () => {
      const newErrors: Record<number, { options?: string; answer?: string; response?: string }> = {};
      let isValid = true;

      for (const row of questions) {
        const key = row.stage_question_mapping_id;
        const rowErrors: { options?: string; answer?: string; response?: string } = {};

        // Dropdown validation
        if (row.answer_type === 'Dropdown (single select)') {
          if (!selections[key]) {
            rowErrors.options = 'Choose one option above!';
            isValid = false;
          }
        } else if (row.answer_type === 'Dropdown (multi select)') {
          if (!selections[key] || (Array.isArray(selections[key]) && selections[key].length === 0)) {
            rowErrors.options = 'Choose one/multiple option(s) above!';
            isValid = false;
          }
        }

        // Text box validation
        const showTextBox = row.answer_type === 'Text Box' || (row.answer_type !== 'None' && row.has_text_box);
        if (showTextBox) {
          if (!answers[key] || !answers[key].trim()) {
            rowErrors.answer = 'Please enter the value.';
            isValid = false;
          } else if (answers[key].includes(' ') && row.answer_type === 'Text Box') {
            rowErrors.answer = 'Spaces not allowed!';
            isValid = false;
          }
        }

        // Response validation — only for non-Basic Details stages
        if (!isBasicDetails) {
          if (!responses[key]) {
            rowErrors.response = 'Select a response!';
            isValid = false;
          }
        }

        if (rowErrors.options || rowErrors.answer || rowErrors.response) {
          newErrors[key] = rowErrors;
        }
      }

      setErrors(newErrors);
      return isValid;
    },
    getAnswers: () => {
      return questions.map((row) => {
        const key = row.stage_question_mapping_id;
        return {
          stage_question_mapping_id: key,
          question_id: row.question_id,
          textbox_value: answers[key] || '',
          question_option_id: typeof selections[key] === 'number' ? selections[key] : null,
          response_answer: responses[key] || '',
          helpers: helpers[key] || [],
        };
      });
    },
  }));

  if (questions.length === 0) {
    return <div style={{ padding: '1rem', color: '#94a3b8', fontSize: '0.78rem' }}>No questions for this stage.</div>;
  }

  return (
    <div style={{ overflow: 'auto' }}>
      <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.78rem' }}>
        <thead>
          <tr style={{ background: '#f8fafc' }}>
            <th style={{ padding: '0.5rem 0.75rem', textAlign: 'center', fontWeight: 700, color: '#475569', width: '3.5rem', borderBottom: '1px solid #e2e8f0' }}>Sr No</th>
            <th style={{ padding: '0.5rem 0.75rem', textAlign: 'left', fontWeight: 700, color: '#475569', borderBottom: '1px solid #e2e8f0' }}>Questions</th>
            <th style={{ padding: '0.5rem 0.75rem', textAlign: 'left', fontWeight: 700, color: '#475569', width: '20rem', borderBottom: '1px solid #e2e8f0' }}>Select Options</th>
            <th style={{ padding: '0.5rem 0.75rem', textAlign: 'left', fontWeight: 700, color: '#475569', width: '14rem', borderBottom: '1px solid #e2e8f0' }}>Enter Answer</th>
            {!isBasicDetails && (
              <th style={{ padding: '0.5rem 0.75rem', textAlign: 'left', fontWeight: 700, color: '#475569', width: '12rem', borderBottom: '1px solid #e2e8f0' }}>Response</th>
            )}
          </tr>
        </thead>
        <tbody>
          {questions.map((row) => {
            const key = row.stage_question_mapping_id;
            const showNA = row.answer_type !== 'Text Box' && (row.answer_type === 'None' || !row.has_text_box);
            const showTextBox = !showNA;
            const rowErr = errors[key];
            return (
              <tr key={key} style={{ borderBottom: '1px solid #f1f5f9' }}>
                <td style={{ padding: '0.5rem 0.75rem', textAlign: 'center', fontWeight: 500 }}>{row.serial_number}</td>
                <td style={{ padding: '0.5rem 0.75rem', color: '#1e293b' }}>{row.question_title}</td>
                <td style={{ padding: '0.5rem 0.75rem' }}>
                  <OptionSelector
                    answerType={row.answer_type}
                    options={row.options}
                    value={selections[key]}
                    onChange={(val) => { setSelections((prev) => ({ ...prev, [key]: val })); setErrors((prev) => { const c = { ...prev }; if (c[key]) { delete c[key].options; if (!c[key].answer) delete c[key]; } return c; }); }}
                  />
                  {rowErr?.options && (
                    <small className="qc-validation-error">{rowErr.options}</small>
                  )}
                </td>
                <td style={{ padding: '0.5rem 0.75rem' }}>
                  {showTextBox ? (
                    <div className="flex flex-column gap-1">
                      <InputText
                        value={answers[key] || ''}
                        className={rowErr?.answer ? 'w-full p-invalid' : 'w-full'}
                        onChange={(e) => { setAnswers((prev) => ({ ...prev, [key]: e.target.value })); setErrors((prev) => { const c = { ...prev }; if (c[key]) { delete c[key].answer; if (!c[key].options) delete c[key]; } return c; }); }}
                        style={{ height: '1.85rem', fontSize: '0.75rem' }}
                      />
                      {rowErr?.answer && (
                        <small className="qc-validation-error">{rowErr.answer}</small>
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
                            style={{ height: '1.85rem', fontSize: '0.75rem' }}
                          />
                          <button type="button"
                            onClick={() => setHelpers((prev) => {
                              const arr = [...(prev[key] || [])];
                              arr.splice(idx, 1);
                              return { ...prev, [key]: arr };
                            })}
                            style={{
                              border: 'none', background: 'transparent', color: 'var(--color-error)',
                              cursor: 'pointer', fontSize: '0.85rem', padding: '0 0.25rem',
                            }}>
                            <i className="pi pi-times" style={{ fontSize: '0.7rem' }} />
                          </button>
                        </div>
                      ))}
                      {/* + Add button */}
                      {row.has_multiple_text_box && canAdd && (
                        <button type="button"
                          onClick={() => setHelpers((prev) => ({ ...prev, [key]: [...(prev[key] || []), ''] }))}
                          style={{
                            border: '1px solid var(--color-primary)', borderRadius: '4px',
                            background: 'transparent', color: 'var(--color-primary)',
                            fontSize: '0.7rem', padding: '0.2rem 0.5rem', cursor: 'pointer',
                            width: 'fit-content',
                          }}>
                          + Add
                        </button>
                      )}
                    </div>
                  ) : (
                    <span style={{ color: '#94a3b8', fontSize: '0.78rem' }}>N/A</span>
                  )}
                </td>
                {!isBasicDetails && (
                  <td style={{ padding: '0.5rem 0.75rem' }}>
                    <div className="flex flex-column">
                      <div className="flex align-items-center gap-3">
                        <div className="flex align-items-center gap-1">
                          <RadioButton name={`response_${key}`} value="YES"
                            checked={responses[key] === 'YES'}
                            onChange={() => { setResponses((prev) => ({ ...prev, [key]: 'YES' })); setErrors((prev) => { const c = { ...prev }; if (c[key]) { delete c[key].response; if (!c[key].options && !c[key].answer) delete c[key]; } return c; }); }} />
                          <label style={{ fontSize: '0.72rem' }}>YES</label>
                        </div>
                        <div className="flex align-items-center gap-1">
                          <RadioButton name={`response_${key}`} value="NO"
                            checked={responses[key] === 'NO'}
                            onChange={() => { setResponses((prev) => ({ ...prev, [key]: 'NO' })); setErrors((prev) => { const c = { ...prev }; if (c[key]) { delete c[key].response; if (!c[key].options && !c[key].answer) delete c[key]; } return c; }); }} />
                          <label style={{ fontSize: '0.72rem' }}>NO</label>
                        </div>
                        <div className="flex align-items-center gap-1">
                          <RadioButton name={`response_${key}`} value="N/A"
                            checked={responses[key] === 'N/A'}
                            onChange={() => { setResponses((prev) => ({ ...prev, [key]: 'N/A' })); setErrors((prev) => { const c = { ...prev }; if (c[key]) { delete c[key].response; if (!c[key].options && !c[key].answer) delete c[key]; } return c; }); }} />
                          <label style={{ fontSize: '0.72rem' }}>N/A</label>
                        </div>
                      </div>
                      {rowErr?.response && (
                        <small className="qc-validation-error">{rowErr.response}</small>
                      )}
                    </div>
                  </td>
                )}
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
});

ChromatographicSnip.displayName = 'ChromatographicSnip';
