/**
 * Sub-question mapping section for QuestionForm — MultiSelect + grid.
 * Visible when has_sub_question toggle is ON.
 */

import { MultiSelect } from 'primereact/multiselect';
import { DataTable } from 'primereact/datatable';
import { Column } from 'primereact/column';

interface QuestionSelectOption {
  label: string;
  value: number;
}

interface Props {
  value: number[];
  questionOptions: QuestionSelectOption[];
  onChange: (ids: number[]) => void;
}

export const QuestionFormSubQuestions = ({ value, questionOptions, onChange }: Props) => (
  <div className="flex flex-column gap-2">
    <label className="font-medium text-sm">Sub Question Mapping</label>
    <MultiSelect value={value} options={questionOptions}
      onChange={(e) => onChange(e.value as number[])} placeholder="Select Sub Questions"
      filter display="chip" className="w-full" />
    {value.length > 0 && (
      <DataTable value={questionOptions.filter((q) => value.includes(q.value))}
        size="small" stripedRows style={{ fontSize: '0.78rem' }}>
        <Column field="label" header="Sub Question" />
      </DataTable>
    )}
  </div>
);
