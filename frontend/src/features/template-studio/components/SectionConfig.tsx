/**
 * SectionConfig — a section nested under a stage. The section name is typed
 * inline (like the Stage Question Mapping page, which creates sections by name
 * rather than selecting them). Each section has its own columns+rows table.
 */

import { InputText } from 'primereact/inputtext';
import { Button } from 'primereact/button';
import type { DesignSection, DesignColumn, DesignRow } from '../models/DesignSpec';
import type { UseDragReorderResult } from '../hooks/useDragReorder';
import { ConfigTable, type QuestionChoice, type MappingContext } from './ConfigTable';

interface Props {
  index: number;
  section: DesignSection;
  questionChoices: QuestionChoice[];
  stageName: string;
  ctx: MappingContext;
  onChange: (section: DesignSection) => void;
  onRemove: () => void;
  onRowDeleted?: (mappingId: number) => void;
  /** Drag handle props from the parent's useDragReorder, for reordering this section among its siblings. */
  dragHandleProps?: ReturnType<UseDragReorderResult['getHandleProps']>;
}

export const SectionConfig = ({
  index,
  section,
  questionChoices,
  stageName,
  ctx,
  onChange,
  onRemove,
  onRowDeleted,
  dragHandleProps,
}: Props) => {
  const setColumns = (columns: DesignColumn[]) => onChange({ ...section, columns });
  const setRows = (rows: DesignRow[]) => onChange({ ...section, rows });

  return (
    <div className="snip-section-block">
      {/* Section name bar */}
      <div className="snip-section-header">
        <div className="snip-section-header-main">
          {dragHandleProps && (
            <span {...dragHandleProps} title="Drag to reorder section" className="snip-section-drag-handle">
              <i className="pi pi-arrows-alt" />
            </span>
          )}
          <div className="snip-section-name-field">
            <label className="block text-xs text-600 font-medium mb-1">Section {index + 1} — Name</label>
            <InputText
              value={section.sectionName}
              onChange={(e) => onChange({ ...section, sectionName: e.target.value })}
              placeholder="e.g. Critical Defects"
              className="w-full"
            />
          </div>
        </div>
        <Button icon="pi pi-trash" rounded text raised severity="danger" size="small"
          onClick={onRemove} type="button" tooltip="Remove section" tooltipOptions={{ position: 'top' }} />
      </div>

      <div className="p-2 pb-3">
        <ConfigTable
          columns={section.columns}
          rows={section.rows}
          questionChoices={questionChoices}
          stageName={stageName}
          ctx={ctx}
          onColumnsChange={setColumns}
          onRowsChange={setRows}
          onRowDeleted={onRowDeleted}
        />
      </div>
    </div>
  );
};
