/**
 * ApprovalSnip — grid component for declaration questions in approval stages.
 * Also shows approval labels (side by side) and a remark dropdown.
 */

import { useState } from 'react';
import { Dropdown } from 'primereact/dropdown';
import { InputTextarea } from 'primereact/inputtextarea';
import { MultiSelect } from 'primereact/multiselect';
import { InputText } from 'primereact/inputtext';
import { useRemarks } from '../../masters/hooks/useRemarks';

const OTHERS_REMARK = 'Others';

interface QuestionAnswerPreview {
  stage_question_mapping_id: number;
  question_id: number;
  question_title: string;
  serial_number: number;
  answer_type: string;
  has_text_box: boolean;
  is_declaration_question: boolean;
  response_options: { id: number; label: string }[];
}

interface ApprovalLabelPreview {
  approval_label_id: number;
  label: string;
}

interface Props {
  questions: QuestionAnswerPreview[];
  approvalLabels: ApprovalLabelPreview[];
  hasDeclarationQuestion: boolean;
}

export const ApprovalSnip = ({ questions, approvalLabels, hasDeclarationQuestion }: Props) => {
  const declarationQuestions = questions.filter((q) => q.is_declaration_question);
  const { data: remarksData } = useRemarks();
  const remarkOptions = (remarksData?.items ?? []).map((r: any) => ({ label: r.remark, value: r.remark }));

  const [answers, setAnswers] = useState<Record<number, any>>({});
  const [selectedRemark, setSelectedRemark] = useState<string | null>(null);
  const [remarkText, setRemarkText] = useState('');

  return (
    <div style={{ paddingTop: '0.75rem' }}>
      {/* Approval Labels — side by side */}
      {approvalLabels.length > 0 && (
        <div style={{ padding: '0.5rem 0.75rem', borderBottom: '1px solid #e2e8f0', background: '#f8fafc' }}
          className="flex align-items-center justify-content-between">
          {approvalLabels.map((al, idx) => (
            <div key={al.approval_label_id}
              style={{
                flex: 1,
                textAlign: idx === 0 ? 'left' : 'right',
                fontSize: '0.78rem',
                fontWeight: 700,
                color: '#475569',
              }}>
              {al.label}
            </div>
          ))}
        </div>
      )}

      {/* Remark dropdown */}
      <div style={{ padding: '0.5rem 0.75rem', maxWidth: '280px' }}>
        <label style={{ fontSize: '0.72rem', fontWeight: 600, color: '#475569', marginBottom: '0.25rem', display: 'block' }}>
          Remark <span style={{ color: 'var(--color-error)' }}>*</span>
        </label>
        <Dropdown
          value={selectedRemark}
          onChange={(e) => { setSelectedRemark(e.value); if (e.value !== OTHERS_REMARK) setRemarkText(''); }}
          placeholder="Select Remark"
          style={{ height: '2rem', fontSize: '0.75rem', width: '100%' }}
          options={remarkOptions}
          filter
          showClear
        />
        {selectedRemark === OTHERS_REMARK && (
          <InputTextarea
            value={remarkText}
            onChange={(e) => setRemarkText(e.target.value)}
            placeholder="Enter remark..."
            rows={2}
            style={{ width: '100%', fontSize: '0.75rem', marginTop: '0.4rem' }}
          />
        )}
      </div>

      {/* Declaration Questions grid */}
      {hasDeclarationQuestion && declarationQuestions.length > 0 && (
        <>
          <div style={{ padding: '0.4rem 0.75rem', fontWeight: 700, fontSize: '0.8rem', color: '#475569', borderBottom: '1px solid #e2e8f0', background: '#f8fafc' }}>
            Declaration Questions
          </div>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.78rem' }}>
            <thead>
              <tr style={{ background: '#f8fafc' }}>
                <th style={{ padding: '0.5rem 0.75rem', textAlign: 'left', fontWeight: 700, color: '#475569', borderBottom: '1px solid #e2e8f0' }}>Question</th>
                <th style={{ padding: '0.5rem 0.75rem', textAlign: 'left', fontWeight: 700, color: '#475569', width: '18rem', borderBottom: '1px solid #e2e8f0' }}>Response Answer</th>
              </tr>
            </thead>
            <tbody>
              {declarationQuestions.map((row) => {
                const key = row.stage_question_mapping_id;
                const showTextBox = row.answer_type === 'Text Box' || row.has_text_box;
                const isMultiSelect = row.answer_type === 'Dropdown (multi select)';
                const isSingleSelect = row.answer_type === 'Dropdown (single select)';
                const isNone = row.answer_type === 'None' && !row.has_text_box;

                const responseOpts = (row.response_options || []).map((o) => ({ label: o.label, value: o.id }));

                return (
                  <tr key={key} style={{ borderBottom: '1px solid #f1f5f9' }}>
                    <td style={{ padding: '0.5rem 0.75rem', color: '#1e293b' }}>{row.question_title}</td>
                    <td style={{ padding: '0.5rem 0.75rem' }}>
                      {isNone ? (
                        <span style={{ color: '#94a3b8', fontSize: '0.78rem' }}>N/A</span>
                      ) : isMultiSelect ? (
                        <MultiSelect
                          value={answers[key] || []}
                          options={responseOpts}
                          onChange={(e) => setAnswers((p) => ({ ...p, [key]: e.value }))}
                          placeholder="Select"
                          filter
                          display="chip"
                          className="w-full"
                          style={{ minHeight: '1.85rem', fontSize: '0.75rem' }}
                        />
                      ) : isSingleSelect ? (
                        <Dropdown
                          value={answers[key] || null}
                          options={responseOpts}
                          onChange={(e) => setAnswers((p) => ({ ...p, [key]: e.value }))}
                          placeholder="Select"
                          filter
                          showClear
                          className="w-full"
                          style={{ height: '1.85rem', fontSize: '0.75rem' }}
                        />
                      ) : showTextBox ? (
                        <InputText
                          value={answers[key] || ''}
                          onChange={(e) => setAnswers((p) => ({ ...p, [key]: e.target.value }))}
                          className="w-full"
                          style={{ height: '1.85rem', fontSize: '0.75rem' }}
                        />
                      ) : (
                        <span style={{ color: '#94a3b8', fontSize: '0.78rem' }}>N/A</span>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </>
      )}
    </div>
  );
};

