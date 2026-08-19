/**
 * SectionStageQuestionGrid — reusable view component showing section questions in a DataTable.
 * Displays question title + sub-questions below it.
 * Used in StageQuestionViewPage for sectioned stages.
 */

import { Column } from 'primereact/column';
import { DataTable } from 'primereact/datatable';
import { MasterRowActions } from '../MasterRowActions';

interface SectionQuestionRow {
  id: number;
  question_id: number;
  serial_number: number;
  aql_limit: string;
}

interface Props {
  questions: SectionQuestionRow[];
  questionMap: Record<number, string>;
  subQuestionIdsMap: Record<number, number[]>;
  onEdit: (row: SectionQuestionRow) => void;
  onDelete: (id: number) => void;
}

export const SectionStageQuestionGrid = ({ questions, questionMap, subQuestionIdsMap, onEdit, onDelete }: Props) => {
  const sorted = [...questions].sort((a, b) => a.serial_number - b.serial_number);

  return (
    <DataTable value={sorted} size="small" stripedRows style={{ fontSize: '0.75rem', marginLeft: '1rem', marginTop: '0.25rem' }}>
      <Column field="serial_number" header="Sr" style={{ width: '3rem' }} />
      <Column header="Question" body={(row: SectionQuestionRow) => (
        <div>
          <span>{questionMap[row.question_id] ?? row.question_id}</span>
          {(subQuestionIdsMap[row.question_id] ?? []).length > 0 && (
            <div style={{ marginTop: '0.2rem', paddingLeft: '0.5rem' }}>
              {(subQuestionIdsMap[row.question_id] ?? []).map((subId) => (
                <div key={subId} style={{ fontSize: '0.7rem', color: '#64748b' }}>
                  • {questionMap[subId] ?? subId}
                </div>
              ))}
            </div>
          )}
        </div>
      )} />
      <Column header="" body={(row: SectionQuestionRow) => (
        <MasterRowActions label="q" canUpdate={true} canDelete={true}
          onEdit={() => onEdit(row)} onDelete={() => onDelete(row.id)} />
      )} style={{ width: '4rem' }} />
    </DataTable>
  );
};
