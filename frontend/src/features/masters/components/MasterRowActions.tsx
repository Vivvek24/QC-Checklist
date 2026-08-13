/**
 * Edit and delete row actions — rounded text raised style.
 */

import { Button } from 'primereact/button';

interface MasterRowActionsProps {
  label: string;
  canUpdate: boolean;
  canDelete: boolean;
  onEdit: () => void;
  onDelete: () => void;
}

export const MasterRowActions = ({
  label,
  canUpdate,
  canDelete,
  onEdit,
  onDelete,
}: MasterRowActionsProps) => (
  <div className="flex gap-2" onClick={(e) => e.stopPropagation()}>
    {canUpdate && (
      <Button
        type="button"
        icon="pi pi-pencil"
        rounded
        text
        raised
        severity="success"
        size="small"
        onClick={(e) => { e.stopPropagation(); onEdit(); }}
        tooltip="Edit"
        tooltipOptions={{ position: 'top' }}
        aria-label={`Edit ${label}`}
      />
    )}
    {canDelete && (
      <Button
        type="button"
        icon="pi pi-trash"
        rounded
        text
        raised
        severity="danger"
        size="small"
        onClick={(e) => { e.stopPropagation(); onDelete(); }}
        tooltip="Delete"
        tooltipOptions={{ position: 'top' }}
        aria-label={`Delete ${label}`}
      />
    )}
  </div>
);
