/**
 * Response Options section for QuestionForm — Add Response Option button + grid + popup.
 * Visible when has_response_option toggle is ON.
 */

import { Button } from 'primereact/button';
import { DataTable } from 'primereact/datatable';
import { Column } from 'primereact/column';
import { QuestionOptionForm, type QuestionOptionFormData } from './QuestionOptionForm';
import { MasterRowActions } from './MasterRowActions';
import type { QuestionOption } from '../models/QuestionOption';
import type { LocalOptionWithTemp } from './QuestionFormOptions';

interface Props {
  localRespOptions: LocalOptionWithTemp[];
  respOptFormVisible: boolean;
  editingRespOption: QuestionOption | null;
  onAddRespOption: () => void;
  onEditRespOption: (idx: number) => void;
  onDeleteRespOption: (idx: number) => void;
  onRespOptFormHide: () => void;
  onRespOptFormSave: (data: QuestionOptionFormData) => void;
}

export const QuestionFormResponseOptions = ({
  localRespOptions,
  respOptFormVisible,
  editingRespOption,
  onAddRespOption,
  onEditRespOption,
  onDeleteRespOption,
  onRespOptFormHide,
  onRespOptFormSave,
}: Props) => (
  <>
    <div className="flex flex-column gap-2">
      <Button type="button" label="Add Response Option" icon="pi pi-plus" size="small"
        outlined onClick={onAddRespOption} className="align-self-start" />
      {localRespOptions.length > 0 && (
        <DataTable value={localRespOptions} size="small" stripedRows
          emptyMessage="No response options." style={{ fontSize: '0.78rem' }}>
          <Column field="option_title" header="Response Option" />
          <Column header="Actions" body={(_row: LocalOptionWithTemp, opts) => (
            <MasterRowActions label={_row.option_title} canUpdate={true} canDelete={true}
              onEdit={() => onEditRespOption(opts.rowIndex)} onDelete={() => onDeleteRespOption(opts.rowIndex)} />
          )} style={{ width: '6rem' }} />
        </DataTable>
      )}
    </div>

    <QuestionOptionForm
      visible={respOptFormVisible}
      initialData={editingRespOption}
      onHide={onRespOptFormHide}
      onSubmit={onRespOptFormSave}
    />
  </>
);
