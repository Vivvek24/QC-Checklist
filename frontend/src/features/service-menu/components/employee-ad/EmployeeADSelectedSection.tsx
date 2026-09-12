/**
 * Employee AD — POST /getselectedemployees section.
 */

import { useState } from 'react';

import { Button } from 'primereact/button';
import { InputText } from 'primereact/inputtext';

import { extractApiError } from '@shared/utils/apiError';

import { useGetSelectedEmployees } from '../../hooks/useEmployeeAD';
import { CollapsibleSection } from '../CollapsibleSection';
import { JsonResultBlock } from '../JsonResultBlock';
import type { ServiceSectionProps } from '../sectionProps';

export const EmployeeADSelectedSection = ({ notify }: ServiceSectionProps) => {
  const [employeeIds, setEmployeeIds] = useState('');
  const getSelectedMutation = useGetSelectedEmployees();

  const handleGetSelected = async () => {
    if (!employeeIds.trim()) {
      notify({
        severity: 'warn',
        summary: 'Validation',
        detail: 'Enter at least one Employee ID',
        life: 3000,
      });
      return;
    }
    const ids = employeeIds
      .split(',')
      .map((id) => id.trim())
      .filter(Boolean);
    try {
      await getSelectedMutation.mutateAsync(ids);
      notify({
        severity: 'success',
        summary: 'Success',
        detail: 'Selected employees fetched',
        life: 3000,
      });
    } catch (error) {
      notify({
        severity: 'error',
        summary: 'Error',
        detail: extractApiError(error, 'Failed to fetch'),
        life: 5000,
      });
    }
  };

  return (
    <CollapsibleSection
      title="POST /getselectedemployees"
      subTitle="Fetch employees by IDs (comma-separated)"
    >
      <div className="grid">
        <div className="col-12 md:col-8">
          <label htmlFor="emp-ids" className="block font-medium mb-2">
            Employee IDs
          </label>
          <InputText
            id="emp-ids"
            value={employeeIds}
            onChange={(e) => setEmployeeIds(e.target.value)}
            placeholder="e.g. 93300040, 93300041"
            className="w-full"
          />
        </div>
        <div className="col-12 md:col-4 flex align-items-end">
          <Button
            label="Fetch Selected"
            icon="pi pi-search"
            onClick={handleGetSelected}
            loading={getSelectedMutation.isPending}
          />
        </div>
      </div>
      <JsonResultBlock data={getSelectedMutation.data} />
    </CollapsibleSection>
  );
};
