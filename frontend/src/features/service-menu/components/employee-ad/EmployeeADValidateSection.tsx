/**
 * Employee AD — POST /validatecredentials section.
 */

import { useState } from 'react';

import { Button } from 'primereact/button';
import { InputText } from 'primereact/inputtext';
import { Password } from 'primereact/password';
import { Tag } from 'primereact/tag';

import { extractApiError } from '@shared/utils/apiError';

import { useValidateCredentials } from '../../hooks/useEmployeeAD';
import { CollapsibleSection } from '../CollapsibleSection';
import type { ServiceSectionProps } from '../sectionProps';

export const EmployeeADValidateSection = ({ notify }: ServiceSectionProps) => {
  const [employeeId, setEmployeeId] = useState('');
  const [password, setPassword] = useState('');
  const validateMutation = useValidateCredentials();

  const handleValidate = async () => {
    if (!employeeId.trim()) {
      notify({
        severity: 'warn',
        summary: 'Validation',
        detail: 'Employee ID is required',
        life: 3000,
      });
      return;
    }
    try {
      const result = await validateMutation.mutateAsync({
        employee_id: employeeId.trim(),
        password: password,
      });
      notify({
        severity: result.is_valid_user ? 'success' : 'warn',
        summary: 'Credential Validation',
        detail: result.is_valid_user
          ? `Employee ${employeeId} is valid`
          : `Employee ${employeeId} validation failed`,
        life: 5000,
      });
    } catch (error) {
      notify({
        severity: 'error',
        summary: 'Error',
        detail: extractApiError(error, 'Failed to validate'),
        life: 5000,
      });
    }
  };

  return (
    <CollapsibleSection
      title="POST /validatecredentials"
      subTitle="Validate employee AD credentials"
    >
      <div className="grid">
        <div className="col-12 md:col-4">
          <label htmlFor="emp-id" className="block font-medium mb-2">
            Employee ID
          </label>
          <InputText
            id="emp-id"
            value={employeeId}
            onChange={(e) => setEmployeeId(e.target.value)}
            placeholder="e.g. 93300040"
            className="w-full"
          />
        </div>
        <div className="col-12 md:col-4">
          <label htmlFor="emp-password" className="block font-medium mb-2">
            Password
          </label>
          <Password
            id="emp-password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="Enter password"
            className="w-full"
            inputClassName="w-full"
            feedback={false}
            toggleMask
          />
        </div>
        <div className="col-12 md:col-4 flex align-items-end">
          <Button
            label="Validate"
            icon="pi pi-check"
            onClick={handleValidate}
            loading={validateMutation.isPending}
          />
        </div>
      </div>
      {validateMutation.data && (
        <div className="mt-3 p-3 surface-100 border-round">
          <div className="flex align-items-center gap-3 mb-2">
            <Tag
              value={validateMutation.data.is_valid_user ? 'Valid User' : 'Invalid User'}
              severity={validateMutation.data.is_valid_user ? 'success' : 'danger'}
              icon={validateMutation.data.is_valid_user ? 'pi pi-check' : 'pi pi-times'}
            />
            <Tag
              value={validateMutation.data.is_success ? 'Success' : 'Failed'}
              severity={validateMutation.data.is_success ? 'success' : 'danger'}
            />
          </div>
          <pre className="text-xs overflow-auto m-0" style={{ maxHeight: '200px' }}>
            {JSON.stringify(validateMutation.data.raw_response, null, 2)}
          </pre>
        </div>
      )}
    </CollapsibleSection>
  );
};
