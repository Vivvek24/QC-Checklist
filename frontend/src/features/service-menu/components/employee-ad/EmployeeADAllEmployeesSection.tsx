/**
 * Employee AD — GET /getemployees section.
 */

import { Button } from 'primereact/button';

import { extractApiError } from '@shared/utils/apiError';

import { useGetEmployees } from '../../hooks/useEmployeeAD';
import { CollapsibleSection } from '../CollapsibleSection';
import { JsonResultBlock } from '../JsonResultBlock';
import type { ServiceSectionProps } from '../sectionProps';

export const EmployeeADAllEmployeesSection = ({ notify }: ServiceSectionProps) => {
  const getEmployeesMutation = useGetEmployees();

  const handleGetAllEmployees = async () => {
    try {
      await getEmployeesMutation.mutateAsync();
      notify({
        severity: 'success',
        summary: 'Success',
        detail: 'All employees fetched',
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
    <CollapsibleSection title="GET /getemployees" subTitle="Fetch all employee records">
      <Button
        label="Get All Employees"
        icon="pi pi-users"
        onClick={handleGetAllEmployees}
        loading={getEmployeesMutation.isPending}
      />
      <JsonResultBlock data={getEmployeesMutation.data} />
    </CollapsibleSection>
  );
};
