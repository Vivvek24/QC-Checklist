/**
 * Options section for QuestionForm — Add Option button + options grid + option popup.
 * Visible when answer_type is 'Dropdown (single select)' or 'Dropdown (multi select)'.
 */

import { Button } from 'primereact/button';
import { DataTable } from 'primereact/datatable';
import { Column } from 'primereact/column';
import { QuestionOptionForm, type QuestionOptionFormData } from './QuestionOptionForm';
import { MasterRowActions } from './MasterRowActions';
import type { QuestionOption } from '../models/QuestionOption';

export interface LocalOption {
  id?: number;
  option_title: string;
  is_active: boolean;
}

export type LocalOptionWithTemp = LocalOption & { tempId: string };

interface Props {
  localOptions: LocalOptionWithTemp[];
  optionFormVisible: boolean;
  editingOption: QuestionOption | null;
  onAddOption: () => void;
  onEditOption: (idx: number) => void;
  onDeleteOption: (idx: number) => void;
  onOptionFormHide: () => void;
  onOptionFormSave: (data: QuestionOptionFormData) => void;
}

export const QuestionFormOptions = ({
  localOptions,
  optionFormVisible,
  editingOption,
  onAddOption,
  onEditOption,
  onDeleteOption,
  onOptionFormHide,
  onOptionFormSave,
}: Props) => (
  <>
    <div className="flex flex-column gap-2">
      <Button type="button" label="Add Option" icon="pi pi-plus" size="small"
        outlined onClick={onAddOption} className="align-self-start" />
      {localOptions.length > 0 && (
        <DataTable value={localOptions} size="small" stripedRows
          emptyMessage="No options." style={{ fontSize: '0.78rem' }}>
          <Column field="option_title" header="Option Title" />
          <Column header="Actions" body={(_row: LocalOptionWithTemp, opts) => (
            <MasterRowActions label={_row.option_title} canUpdate={true} canDelete={true}
              onEdit={() => onEditOption(opts.rowIndex)} onDelete={() => onDeleteOption(opts.rowIndex)} />
          )} style={{ width: '6rem' }} />
        </DataTable>
      )}
    </div>

    <QuestionOptionForm
      visible={optionFormVisible}
      initialData={editingOption}
      onHide={onOptionFormHide}
      onSubmit={onOptionFormSave}
    />
  </>
);
