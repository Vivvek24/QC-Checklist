/**
 * Published Darwin AD — GET /getemployees section.
 */

import { useState } from 'react';

import { Button } from 'primereact/button';
import { InputText } from 'primereact/inputtext';

import { CollapsibleSection } from '@features/service-menu/components/CollapsibleSection';
import { JsonResultBlock } from '@features/service-menu/components/JsonResultBlock';

import { extractApiError } from '@shared/utils/apiError';

import { usePublishedGetEmployees } from '../../hooks/usePublishedDarwinAd';
import type { PublishedSectionProps } from '../publishedSectionProps';

export const PublishedGetEmployeesSection = ({ notify, apiKey }: PublishedSectionProps) => {
  const [status, setStatus] = useState('');
  const mutation = usePublishedGetEmployees();

  const handleRun = async () => {
    try {
      await mutation.mutateAsync({ apiKey, status });
      notify({ severity: 'success', summary: 'Success', detail: 'Employees fetched', life: 3000 });
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
      title="GET /getemployees"
      subTitle="All employees in the Darwin AD envelope (optional status filter)"
    >
      <div className="grid">
        <div className="col-12 md:col-8">
          <label htmlFor="ge-status" className="block font-medium mb-2">
            Status filter <span className="text-500 font-normal">(optional)</span>
          </label>
          <InputText
            id="ge-status"
            value={status}
            onChange={(e) => setStatus(e.target.value)}
            placeholder="e.g. Active"
            className="w-full"
          />
        </div>
        <div className="col-12 md:col-4 flex align-items-end">
          <Button
            label="Fetch Employees"
            icon="pi pi-download"
            onClick={handleRun}
            loading={mutation.isPending}
          />
        </div>
      </div>
      <JsonResultBlock data={mutation.data} />
    </CollapsibleSection>
  );
};
