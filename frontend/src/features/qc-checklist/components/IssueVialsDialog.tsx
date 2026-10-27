/**
 * IssueVialsDialog — small popup shown when "Issue Vials" is clicked on a row.
 *
 * Shows a single dropdown of analyst-role users ("Issued By"). On confirm it
 * calls onIssue with the picked user id. Users are loaded from
 * GET /users/by-role?role_code=ANALYST.
 */

import { useEffect, useState } from 'react';
import { Dialog } from 'primereact/dialog';
import { Dropdown } from 'primereact/dropdown';
import { Button } from 'primereact/button';
import { qcChecklistApi, type RoleUserResponse } from '../api/qcChecklistApi';

interface Props {
  visible: boolean;
  onHide: () => void;
  /** Called with the chosen analyst user id when the user confirms. */
  onIssue: (userId: number) => void;
}

export const IssueVialsDialog = ({ visible, onHide, onIssue }: Props) => {
  const [users, setUsers] = useState<RoleUserResponse[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedUserId, setSelectedUserId] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Load analyst users each time the dialog opens.
  useEffect(() => {
    if (!visible) return;
    setSelectedUserId(null);
    setError(null);
    setLoading(true);
    qcChecklistApi
      .listUsersByRole('ANALYST')
      .then(setUsers)
      .catch(() => setUsers([]))
      .finally(() => setLoading(false));
  }, [visible]);

  const options = users.map((u) => ({
    label: u.employee_name || u.username,
    value: u.id,
  }));

  const handleIssue = () => {
    if (selectedUserId == null) {
      // Mirrors the Mendix inline validation on an empty receiver.
      setError('Please Select Analyst Name!');
      return;
    }
    onIssue(selectedUserId);
    onHide();
  };

  const footer = (
    <div className="flex justify-content-end gap-2">
      <Button label="Cancel" icon="pi pi-times" severity="secondary" outlined size="small" type="button" onClick={onHide} />
      <Button label="Issue" icon="pi pi-check" size="small" type="button" onClick={handleIssue} />
    </div>
  );

  return (
    <Dialog
      header="Issue Vials"
      visible={visible}
      onHide={onHide}
      footer={footer}
      style={{ width: '22rem' }}
      modal
      dismissableMask
    >
      <div className="flex flex-column gap-2">
        <label className="text-sm font-medium" style={{ color: '#475569' }}>Issued By</label>
        <Dropdown
          value={selectedUserId}
          options={options}
          onChange={(e) => { setSelectedUserId(e.value); setError(null); }}
          placeholder={loading ? 'Loading users...' : 'Select analyst'}
          disabled={loading}
          filter
          showClear
          className={error ? 'w-full p-invalid' : 'w-full'}
          emptyMessage="No analyst users"
        />
        {error && <small className="qc-validation-error">{error}</small>}
      </div>
    </Dialog>
  );
};
