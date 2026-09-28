/**
 * StageConfig — one stage block on the design canvas. The stage is chosen from
 * a dropdown of the stages mapped to the format. It has its own columns+rows
 * table (ConfigTable) and, optionally, nested sections — each section chosen
 * from the stage's mapped sections with its own table.
 */

import { Dropdown } from 'primereact/dropdown';
import { Button } from 'primereact/button';
import { InputSwitch } from 'primereact/inputswitch';
import { Tag } from 'primereact/tag';
import { BASIC_DETAILS_STAGE } from '@features/masters/constants';
import { useDragReorder } from '../hooks/useDragReorder';
import type { DesignStage, DesignColumn, DesignRow, DesignSection } from '../models/DesignSpec';
import { emptySection } from '../models/DesignSpec';
import { ConfigTable, type QuestionChoice, type MappingContext } from './ConfigTable';
import { SectionConfig } from './SectionConfig';

export interface StageOption {
  /** The stage's format_stage_mapping id, if one already exists for this
   * format. Null when the stage has never been saved for this format yet —
   * Save Configuration creates the mapping automatically in that case. */
  fsmId: number | null;
  stageId: number;
  stageName: string;
  /** Approval labels already mapped to this stage (read-only display). */
  approvalLabels: { id: number; label: string }[];
  /** format_stage_mappings.has_section for this stage, as currently saved. */
  hasSection: boolean;
}

export type { QuestionChoice, MappingContext } from './ConfigTable';

interface Props {
  index: number;
  stage: DesignStage;
  stageOptions: StageOption[];
  questionChoices: QuestionChoice[];
  ctx: MappingContext;
  onChange: (stage: DesignStage) => void;
  onRemove: () => void;
  /** Bubbled up when a saved row's mapping should be deleted on Save. */
  onRowDeleted?: (mappingId: number) => void;
  /** Bubbled up when a saved section (and its rows) should be deleted on Save. */
  onSectionDeleted?: (section: DesignSection) => void;
  /**
   * Persist a has_section change immediately (PATCH /masters/format-stage-mappings),
   * mirroring the Stage Question Mapping page's toggle. Called with the
   * stage's fsmId and the new value.
   */
  onToggleHasSection?: (fsmId: number, value: boolean) => void;
}

export const StageConfig = ({
  index,
  stage,
  stageOptions,
  questionChoices,
  ctx,
  onChange,
  onRemove,
  onRowDeleted,
  onSectionDeleted,
  onToggleHasSection,
}: Props) => {
  const stageDropdownOptions = stageOptions.map((s) => ({ label: s.stageName, value: s.stageId }));

  const pickStage = (stageId: number | null) => {
    const picked = stageOptions.find((s) => s.stageId === stageId);
    onChange({
      ...stage,
      stageFsmId: picked?.fsmId ?? null,
      stageId: picked?.stageId ?? null,
      stageName: picked?.stageName ?? '',
      hasSection: picked?.hasSection ?? false,
    });
  };

  const isBasicDetails = stage.stageName === BASIC_DETAILS_STAGE;

  const toggleHasSection = (value: boolean) => {
    onChange({ ...stage, hasSection: value });
    if (stage.stageFsmId != null) onToggleHasSection?.(stage.stageFsmId, value);
  };

  // Approval labels already mapped to the picked stage (read-only).
  const approvalLabels =
    stageOptions.find((s) => s.stageId === stage.stageId)?.approvalLabels ?? [];

  const setColumns = (columns: DesignColumn[]) => onChange({ ...stage, columns });
  const setRows = (rows: DesignRow[]) => onChange({ ...stage, rows });

  const setSections = (sections: DesignSection[]) => onChange({ ...stage, sections });
  const addSection = () => setSections([...stage.sections, emptySection()]);
  const updateSection = (key: string, section: DesignSection) =>
    setSections(stage.sections.map((s) => (s.key === key ? section : s)));
  const removeSection = (key: string) => {
    const section = stage.sections.find((s) => s.key === key);
    if (section) onSectionDeleted?.(section);
    setSections(stage.sections.filter((s) => s.key !== key));
  };

  // Drag-and-drop reordering for sections — native HTML5 DnD via the shared hook.
  const sectionDrag = useDragReorder<DesignSection>({ items: stage.sections, onReorder: setSections });

  return (
    <div className="surface-card border-round shadow-1 mb-3 snip-stage-block">
      {/* Stage selector bar */}
      <div className="flex align-items-end justify-content-between gap-2 p-2 snip-stage-header">
        <div className="snip-stage-name-field">
          <label className="block text-xs text-600 font-medium mb-1">Stage {index + 1}</label>
          <Dropdown
            value={stage.stageId}
            options={stageDropdownOptions}
            onChange={(e) => pickStage(e.value)}
            placeholder="Select a stage"
            className="w-full"
            filter
            emptyMessage="No stages for this format"
          />
        </div>
        <div className="flex align-items-center gap-3">
          {stage.stageId != null && !isBasicDetails && (
            <div className="flex align-items-center gap-2">
              <InputSwitch checked={stage.hasSection} onChange={(e) => toggleHasSection(e.value ?? false)} />
              <span className="text-xs text-600">Has Section</span>
            </div>
          )}
          <Button icon="pi pi-trash" rounded text raised severity="danger" size="small"
            onClick={onRemove} type="button" tooltip="Remove stage" tooltipOptions={{ position: 'top' }} />
        </div>
      </div>

      <div className="p-3">
        {/* Stage-level table — hidden while sectioned, matching the Stage
            Question Mapping page's mutual exclusivity between direct rows
            and sections for the same stage. */}
        {!stage.hasSection && (
          <ConfigTable
            columns={stage.columns}
            rows={stage.rows}
            questionChoices={questionChoices}
            stageName={stage.stageName}
            ctx={ctx}
            onColumnsChange={setColumns}
            onRowsChange={setRows}
            onRowDeleted={onRowDeleted}
          />
        )}

        {/* Nested sections — only while this stage is sectioned. */}
        {stage.hasSection && stage.sections.length > 0 && (
          <div className="mt-3">
            {stage.sections.map((sec, i) => (
              <div
                key={sec.key}
                {...sectionDrag.getItemProps(i)}
                className={`snip-section-drop-target${sectionDrag.dragOverIndex === i ? ' snip-section-drop-target--over' : ''}`}
                style={{ opacity: sectionDrag.draggingIndex === i ? 0.5 : 1 }}
              >
                <SectionConfig
                  index={i}
                  section={sec}
                  questionChoices={questionChoices}
                  stageName={stage.stageName}
                  ctx={ctx}
                  onChange={(next) => updateSection(sec.key, next)}
                  onRemove={() => removeSection(sec.key)}
                  onRowDeleted={onRowDeleted}
                  dragHandleProps={sectionDrag.getHandleProps(i)}
                />
              </div>
            ))}
          </div>
        )}

        {stage.hasSection && (
          <Button
            icon="pi pi-folder-plus"
            rounded raised
            onClick={addSection}
            type="button"
            className="mt-3 snip-add-btn snip-add-btn--section"
            aria-label="Add Section"
            tooltip="Add Section"
            tooltipOptions={{ position: 'top' }}
          />
        )}

        {/* Approval labels — auto-populated from the stage's existing mapping (read-only) */}
        {stage.stageId != null && (
          <div className="mt-3 pt-3 snip-stage-sections-wrap">
            <div className="text-xs text-600 font-medium mb-2">
              Approval Labels <span className="text-500">(from stage mapping)</span>
            </div>
            {approvalLabels.length === 0 ? (
              <span className="text-500 text-sm">No approval labels mapped to this stage.</span>
            ) : (
              <div className="flex flex-wrap gap-2">
                {approvalLabels.map((a) => (
                  <Tag key={a.id} value={a.label} severity="info" />
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
