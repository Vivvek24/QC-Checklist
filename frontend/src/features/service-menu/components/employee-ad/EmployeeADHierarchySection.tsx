/**
 * Employee AD — GET /getHierarchyData section.
 */

import { Button } from 'primereact/button';

import { extractApiError } from '@shared/utils/apiError';

import { useGetHierarchy } from '../../hooks/useEmployeeAD';
import { CollapsibleSection } from '../CollapsibleSection';
import { JsonResultBlock } from '../JsonResultBlock';
import type { ServiceSectionProps } from '../sectionProps';

export const EmployeeADHierarchySection = ({ notify }: ServiceSectionProps) => {
  const getHierarchyMutation = useGetHierarchy();

  const handleGetHierarchy = async () => {
    try {
      await getHierarchyMutation.mutateAsync();
      notify({
        severity: 'success',
        summary: 'Success',
        detail: 'Hierarchy data fetched',
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
      title="GET /getHierarchyData"
      subTitle="Fetch organizational hierarchy data"
    >
      <Button
        label="Get Hierarchy"
        icon="pi pi-sitemap"
        onClick={handleGetHierarchy}
        loading={getHierarchyMutation.isPending}
      />
      <JsonResultBlock data={getHierarchyMutation.data} />
    </CollapsibleSection>
  );
};
