/**
 * Published Darwin AD — POST /getselectedemployees section.
 */

import { useState } from 'react';

import { Button } from 'primereact/button';
import { InputText } from 'primereact/inputtext';

import { CollapsibleSection } from '@features/service-menu/components/CollapsibleSection';
import { JsonResultBlock } from '@features/service-menu/components/JsonResultBlock';

import { extractApiError } from '@shared/utils/apiError';

import { usePublishedGetSelectedEmployees } from '../../hooks/usePublishedDarwinAd';
import type { PublishedSectionProps } from '../publishedSectionProps';

export const PublishedSelectedEmployeesSection = ({ notify, apiKey }: PublishedSectionProps) => {
  const [employeeIds, setEmployeeIds] = useState('');
  const mutation = usePublishedGetSelectedEmployees();

  const handleRun = async () => {
    if (!employeeIds.trim()) {
      notify({
        severity: 'warn',
        summary: 'Validation',
        detail: 'Enter at least one id or email',
        life: 3000,
      });
      return;
    }
    try {
      await mutation.mutateAsync({ apiKey, employeeIds });
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
        detail: extractApiError(error, error instanceof Error ? error.message : 'Request failed'),
        life: 5000,
      });
    }
  };

  return (
    <CollapsibleSection
      title="POST /getselectedemployees"
      subTitle="Employees by comma-separated ids or company emails (form: EmployeeIDs)"
    >
      <div className="grid">
        <div className="col-12 md:col-8">
          <label htmlFor="se-ids" className="block font-medium mb-2">
            EmployeeIDs
          </label>
          <InputText
            id="se-ids"
            value={employeeIds}
            onChange={(e) => setEmployeeIds(e.target.value)}
            placeholder="e.g. 93300040, jane.doe@emcure.com"
            className="w-full"
          />
        </div>
        <div className="col-12 md:col-4 flex align-items-end">
          <Button
            label="Fetch Selected"
            icon="pi pi-search"
            onClick={handleRun}
            loading={mutation.isPending}
          />
        </div>
      </div>
      <JsonResultBlock data={mutation.data} />
    </CollapsibleSection>
  );
};
