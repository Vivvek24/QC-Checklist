/**
 * StageQuestionGrid — reusable view component showing stage questions in a DataTable.
 * Used in StageQuestionViewPage for non-sectioned stages.
 */

import { Column } from 'primereact/column';
import { DataTable } from 'primereact/datatable';
import { MasterRowActions } from '../MasterRowActions';

interface StageQuestionRow {
  id: number;
  question_id: number;
  serial_number: number;
  show_on_grid: boolean;
  aql_limit: string;
}

interface Props {
  questions: StageQuestionRow[];
  questionMap: Record<number, string>;
  onEdit: (row: StageQuestionRow) => void;
  onDelete: (id: number) => void;
}

export const StageQuestionGrid = ({ questions, questionMap, onEdit, onDelete }: Props) => {
  const sorted = [...questions].sort((a, b) => a.serial_number - b.serial_number);

  return (
    <DataTable value={sorted} size="small" stripedRows style={{ fontSize: '0.78rem', marginLeft: '1rem' }}>
      <Column field="serial_number" header="Sr No" style={{ width: '4rem' }} />
      <Column header="Question" body={(row: StageQuestionRow) => questionMap[row.question_id] ?? row.question_id} />
      <Column header="Actions" body={(row: StageQuestionRow) => (
        <MasterRowActions label="question" canUpdate={true} canDelete={true}
          onEdit={() => onEdit(row)} onDelete={() => onDelete(row.id)} />
      )} style={{ width: '5rem' }} />
    </DataTable>
  );
};
