/**
 * AQLSnip — grid component for AQL format type checklist.
 *
 * Basic Details stage: Sr No | Question | Enter Answer (with add helper)
 * Section stages: Sr No | Defects (question + sub-questions) | AQL Limit | Observed Defects (text box + helpers)
 */

import { useState } from 'react';
import { InputText } from 'primereact/inputtext';
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
  has_sub_question: boolean;
  aql_limit: string;
  sub_questions: QuestionAnswerPreview[];
  options: { id: number; label: string }[];
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

export const AQLSnip = ({ questions, sections, stageName, stageStatus, hasSection }: Props) => {
  const isBasicDetails = stageName === 'Basic Details';
  const canAdd = stageStatus === 'Initial' || stageStatus === 'Draft' || stageStatus === 'ReferBack';

  const [answers, setAnswers] = useState<Record<number, string>>({});
  const [helpers, setHelpers] = useState<Record<number, string[]>>({});
  const [selections, setSelections] = useState<Record<number, any>>({});

  // Basic Details — same as Chromatographic: Sr No | Question | Select Options | Enter Answer
  if (isBasicDetails) {
    return (
      <div style={{ overflow: 'auto' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.78rem' }}>
          <thead>
            <tr style={{ background: '#f8fafc' }}>
              <th style={{ padding: '0.5rem 0.75rem', textAlign: 'center', fontWeight: 700, color: '#475569', width: '3.5rem', borderBottom: '1px solid #e2e8f0' }}>Sr No</th>
              <th style={{ padding: '0.5rem 0.75rem', textAlign: 'left', fontWeight: 700, color: '#475569', borderBottom: '1px solid #e2e8f0' }}>Questions</th>
              <th style={{ padding: '0.5rem 0.75rem', textAlign: 'left', fontWeight: 700, color: '#475569', width: '18rem', borderBottom: '1px solid #e2e8f0' }}>Select Options</th>
              <th style={{ padding: '0.5rem 0.75rem', textAlign: 'left', fontWeight: 700, color: '#475569', width: '14rem', borderBottom: '1px solid #e2e8f0' }}>Enter Answer</th>
            </tr>
          </thead>
          <tbody>
            {questions.map((row) => {
              const key = row.stage_question_mapping_id;
              const showNA = row.answer_type !== 'Text Box' && (row.answer_type === 'None' || !row.has_text_box);
              const showTextBox = !showNA;
              return (
                <tr key={key} style={{ borderBottom: '1px solid #f1f5f9' }}>
                  <td style={{ padding: '0.5rem 0.75rem', textAlign: 'center', fontWeight: 500 }}>{row.serial_number}</td>
                  <td style={{ padding: '0.5rem 0.75rem', color: '#1e293b' }}>{row.question_title}</td>
                  <td style={{ padding: '0.5rem 0.75rem' }}>
                    <OptionSelector answerType={row.answer_type} options={row.options}
                      value={selections[key]} onChange={(val) => setSelections((p) => ({ ...p, [key]: val }))} />
                  </td>
                  <td style={{ padding: '0.5rem 0.75rem' }}>
                    {showTextBox ? (
                      <div className="flex flex-column gap-1">
                        <InputText value={answers[key] || ''} className="w-full"
                          onChange={(e) => setAnswers((p) => ({ ...p, [key]: e.target.value }))}
                          style={{ height: '1.85rem', fontSize: '0.75rem' }} />
                        {(helpers[key] || []).map((val, idx) => (
                          <div key={idx} className="flex align-items-center gap-1">
                            <InputText value={val} className="flex-1"
                              onChange={(e) => setHelpers((p) => { const a = [...(p[key] || [])]; a[idx] = e.target.value; return { ...p, [key]: a }; })}
                              style={{ height: '1.85rem', fontSize: '0.75rem' }} />
                            <button type="button" onClick={() => setHelpers((p) => { const a = [...(p[key] || [])]; a.splice(idx, 1); return { ...p, [key]: a }; })}
                              style={{ border: 'none', background: 'transparent', color: 'var(--color-error)', cursor: 'pointer' }}>
                              <i className="pi pi-times" style={{ fontSize: '0.7rem' }} />
                            </button>
                          </div>
                        ))}
                        {row.has_multiple_text_box && canAdd && (
                          <button type="button" onClick={() => setHelpers((p) => ({ ...p, [key]: [...(p[key] || []), ''] }))}
                            style={{ border: '1px solid var(--color-primary)', borderRadius: '4px', background: 'transparent', color: 'var(--color-primary)', fontSize: '0.7rem', padding: '0.2rem 0.5rem', cursor: 'pointer', width: 'fit-content' }}>
                            + Add
                          </button>
                        )}
                      </div>
                    ) : (
                      <span style={{ color: '#94a3b8', fontSize: '0.78rem' }}>N/A</span>
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

  // Section stages — show sections with: Sr No | Defects | AQL Limit | Observed Defects
  return (
    <div style={{ overflow: 'auto' }}>
      {(hasSection ? sections : [{ section_id: 0, section_name: '', questions }]).map((section) => (
        <div key={section.section_id}>
          {hasSection && section.section_name && (
            <div style={{ padding: '0.5rem 0.75rem', fontWeight: 700, fontSize: '0.8rem', color: 'var(--color-primary)', background: '#fef2f2', borderBottom: '1px solid #fecaca' }}>
              {section.section_name}
            </div>
          )}
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.78rem' }}>
            <thead>
              <tr style={{ background: '#f8fafc' }}>
                <th style={{ padding: '0.5rem 0.75rem', textAlign: 'center', fontWeight: 700, color: '#475569', width: '3.5rem', borderBottom: '1px solid #e2e8f0' }}>Sr No</th>
                <th style={{ padding: '0.5rem 0.75rem', textAlign: 'left', fontWeight: 700, color: '#475569', borderBottom: '1px solid #e2e8f0' }}>Defects</th>
                <th style={{ padding: '0.5rem 0.75rem', textAlign: 'center', fontWeight: 700, color: '#475569', width: '6rem', borderBottom: '1px solid #e2e8f0' }}>AQL Limit</th>
                <th style={{ padding: '0.5rem 0.75rem', textAlign: 'left', fontWeight: 700, color: '#475569', width: '16rem', borderBottom: '1px solid #e2e8f0' }}>Observed Defects</th>
              </tr>
            </thead>
            <tbody>
              {section.questions.map((row) => {
                const key = row.stage_question_mapping_id;
                const showNA = row.answer_type !== 'Text Box' && (row.answer_type === 'None' || !row.has_text_box);
                const showTextBox = !showNA;
                return (
                  <tr key={key} style={{ borderBottom: '1px solid #f1f5f9' }}>
                    <td style={{ padding: '0.5rem 0.75rem', textAlign: 'center', fontWeight: 500 }}>{row.serial_number}</td>
                    {/* Defects — question title + sub-questions below */}
                    <td style={{ padding: '0.5rem 0.75rem', color: '#1e293b' }}>
                      <div>{row.question_title}</div>
                      {row.has_sub_question && row.sub_questions.length > 0 && (
                        <div style={{ marginTop: '0.3rem', paddingLeft: '0.75rem' }}>
                          {row.sub_questions.map((sub) => (
                            <div key={sub.question_id} style={{ fontSize: '0.72rem', color: '#64748b', marginBottom: '0.2rem' }}>
                              • {sub.question_title}
                            </div>
                          ))}
                        </div>
                      )}
                    </td>
                    {/* AQL Limit */}
                    <td style={{ padding: '0.5rem 0.75rem', textAlign: 'center', color: '#475569', fontWeight: 500 }}>
                      {row.aql_limit ? parseFloat(row.aql_limit).toString() : '-'}
                    </td>
                    {/* Observed Defects */}
                    <td style={{ padding: '0.5rem 0.75rem' }}>
                      <div className="flex flex-column gap-1">
                        {/* Main question answer box — based on parent's own answer_type */}
                        {showTextBox ? (
                          <>
                            <InputText value={answers[key] || ''} className="w-full"
                              onChange={(e) => setAnswers((p) => ({ ...p, [key]: e.target.value }))}
                              style={{ height: '1.85rem', fontSize: '0.75rem' }} />
                            {/* Main answer helpers */}
                            {(helpers[key] || []).map((val, idx) => (
                              <div key={idx} className="flex align-items-center gap-1">
                                <InputText value={val} className="flex-1"
                                  onChange={(e) => setHelpers((p) => { const a = [...(p[key] || [])]; a[idx] = e.target.value; return { ...p, [key]: a }; })}
                                  style={{ height: '1.85rem', fontSize: '0.75rem' }} />
                                <button type="button" onClick={() => setHelpers((p) => { const a = [...(p[key] || [])]; a.splice(idx, 1); return { ...p, [key]: a }; })}
                                  style={{ border: 'none', background: 'transparent', color: 'var(--color-error)', cursor: 'pointer' }}>
                                  <i className="pi pi-times" style={{ fontSize: '0.7rem' }} />
                                </button>
                              </div>
                            ))}
                            {row.has_multiple_text_box && canAdd && (
                              <button type="button" onClick={() => setHelpers((p) => ({ ...p, [key]: [...(p[key] || []), ''] }))}
                                style={{ border: '1px solid var(--color-primary)', borderRadius: '4px', background: 'transparent', color: 'var(--color-primary)', fontSize: '0.7rem', padding: '0.2rem 0.5rem', cursor: 'pointer', width: 'fit-content' }}>
                                + Add
                              </button>
                            )}
                          </>
                        ) : (
                          <span style={{ color: '#94a3b8', fontSize: '0.78rem' }}>N/A</span>
                        )}
                        {/* Sub-question answer boxes — each evaluated by its own answer_type */}
                        {row.has_sub_question && row.sub_questions.map((sub) => {
                          const subKey = sub.stage_question_mapping_id || sub.question_id + 100000;
                          const subShowNA = sub.answer_type !== 'Text Box' && (sub.answer_type === 'None' || !sub.has_text_box);
                          if (subShowNA) return null;
                          return (
                            <div key={subKey}>
                              <InputText value={answers[subKey] || ''} className="w-full aql-sub-input"
                                placeholder={sub.question_title}
                                onChange={(e) => setAnswers((p) => ({ ...p, [subKey]: e.target.value }))}
                                style={{ height: '1.7rem', fontSize: '0.68rem' }} />
                              {/* Sub-answer helpers */}
                              {(helpers[subKey] || []).map((val, idx) => (
                                <div key={idx} className="flex align-items-center gap-1 mt-1">
                                  <InputText value={val} className="flex-1"
                                    onChange={(e) => setHelpers((p) => { const a = [...(p[subKey] || [])]; a[idx] = e.target.value; return { ...p, [subKey]: a }; })}
                                    style={{ height: '1.85rem', fontSize: '0.72rem' }} />
                                  <button type="button" onClick={() => setHelpers((p) => { const a = [...(p[subKey] || [])]; a.splice(idx, 1); return { ...p, [subKey]: a }; })}
                                    style={{ border: 'none', background: 'transparent', color: 'var(--color-error)', cursor: 'pointer' }}>
                                    <i className="pi pi-times" style={{ fontSize: '0.7rem' }} />
                                  </button>
                                </div>
                              ))}
                              {sub.has_multiple_text_box && canAdd && (
                                <button type="button" onClick={() => setHelpers((p) => ({ ...p, [subKey]: [...(p[subKey] || []), ''] }))}
                                  style={{ border: '1px solid var(--color-primary)', borderRadius: '4px', background: 'transparent', color: 'var(--color-primary)', fontSize: '0.65rem', padding: '0.15rem 0.4rem', cursor: 'pointer', width: 'fit-content', marginTop: '0.2rem' }}>
                                  + Add
                                </button>
                              )}
                            </div>
                          );
                        })}
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      ))}
    </div>
  );
};
