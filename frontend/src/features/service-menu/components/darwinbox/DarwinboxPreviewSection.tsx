/**
 * Darwinbox — Preview section.
 * Fetches a dataset from Darwinbox without persisting (for verification).
 */

import { useState } from 'react';

import { Button } from 'primereact/button';
import { Dialog } from 'primereact/dialog';
import { Dropdown } from 'primereact/dropdown';
import { ProgressSpinner } from 'primereact/progressspinner';
import { Tag } from 'primereact/tag';

import { extractApiError } from '@shared/utils/apiError';

import type { DarwinboxDataset } from '../../api/darwinboxApi';
import { useFetchDarwinboxEmployees } from '../../hooks/useDarwinbox';
import { CollapsibleSection } from '../CollapsibleSection';
import type { ServiceSectionProps } from '../sectionProps';

const FETCH_DATASETS: { label: string; value: DarwinboxDataset }[] = [
  { label: 'Active', value: 'active' },
  { label: 'Inactive', value: 'inactive' },
];

export const DarwinboxPreviewSection = ({ notify }: ServiceSectionProps) => {
  const [fetchDataset, setFetchDataset] = useState<DarwinboxDataset>('active');
  const fetchMutation = useFetchDarwinboxEmployees();

  const handleFetch = async () => {
    try {
      const result = await fetchMutation.mutateAsync(fetchDataset);
      notify({
        severity: 'success',
        summary: 'Fetched',
        detail: `${result.count} ${fetchDataset} employees returned by Darwinbox`,
        life: 4000,
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

  const isBusy = fetchMutation.isPending;

  return (
    <CollapsibleSection
      title="Preview from Darwinbox"
      subTitle="Fetch a dataset without saving (for verification)"
    >
      {/* Blocking overlay while a long-running Darwinbox call is in progress */}
      <Dialog
        visible={isBusy}
        modal
        closable={false}
        draggable={false}
        resizable={false}
        showHeader={false}
        onHide={() => {}}
        contentClassName="border-round"
        style={{ width: '420px' }}
      >
        <div className="flex flex-column align-items-center gap-3 py-4 text-center">
          <ProgressSpinner style={{ width: '48px', height: '48px' }} strokeWidth="4" />
          <span className="font-semibold text-900">Fetching data</span>
          <span className="text-600 text-sm">
            Fetching employees from Darwinbox. This can take a while for large datasets. Please keep
            this tab open.
          </span>
        </div>
      </Dialog>

      <div className="grid">
        <div className="col-12 md:col-4">
          <label htmlFor="fetch-dataset" className="block font-medium mb-2">
            Dataset
          </label>
          <Dropdown
            inputId="fetch-dataset"
            value={fetchDataset}
            options={FETCH_DATASETS}
            onChange={(e) => setFetchDataset(e.value)}
            className="w-full"
          />
        </div>
        <div className="col-12 md:col-4 flex align-items-end">
          <Button
            label="Fetch Preview"
            icon="pi pi-search"
            severity="secondary"
            onClick={handleFetch}
            loading={fetchMutation.isPending}
          />
        </div>
      </div>
      {fetchMutation.data && (
        <div className="mt-3 p-3 surface-100 border-round">
          <div className="flex align-items-center justify-content-between mb-2">
            <span className="font-semibold text-sm text-600">
              {fetchMutation.data.count} records ({fetchMutation.data.dataset})
            </span>
            <Tag value={fetchMutation.data.message} severity="success" />
          </div>
          <pre className="text-xs overflow-auto m-0" style={{ maxHeight: '300px' }}>
            {JSON.stringify(fetchMutation.data.employee_data.slice(0, 5), null, 2)}
          </pre>
        </div>
      )}
    </CollapsibleSection>
  );
};
