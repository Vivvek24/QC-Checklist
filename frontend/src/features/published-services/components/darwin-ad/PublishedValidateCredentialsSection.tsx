/**
 * Published Darwin AD — POST /validatecredentials section.
 */

import { useState } from 'react';

import { Button } from 'primereact/button';
import { InputText } from 'primereact/inputtext';
import { Password } from 'primereact/password';

import { CollapsibleSection } from '@features/service-menu/components/CollapsibleSection';
import { JsonResultBlock } from '@features/service-menu/components/JsonResultBlock';

import { extractApiError } from '@shared/utils/apiError';

import { usePublishedValidateCredentials } from '../../hooks/usePublishedDarwinAd';
import type { PublishedSectionProps } from '../publishedSectionProps';

export const PublishedValidateCredentialsSection = ({ notify, apiKey }: PublishedSectionProps) => {
  const [employeeId, setEmployeeId] = useState('');
  const [password, setPassword] = useState('');
  const mutation = usePublishedValidateCredentials();

  const handleRun = async () => {
    if (!employeeId.trim() || !password) {
      notify({
        severity: 'warn',
        summary: 'Validation',
        detail: 'Enter Employee ID and password',
        life: 3000,
      });
      return;
    }
    try {
      await mutation.mutateAsync({ apiKey, employeeId, password });
      notify({ severity: 'success', summary: 'Done', detail: 'Validation completed', life: 3000 });
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
      title="POST /validatecredentials"
      subTitle="Validate credentials against configured LDAP servers (form: EmployeeId, Password)"
    >
      <div className="grid">
        <div className="col-12 md:col-5">
          <label htmlFor="vc-id" className="block font-medium mb-2">
            EmployeeId
          </label>
          <InputText
            id="vc-id"
            value={employeeId}
            onChange={(e) => setEmployeeId(e.target.value)}
            placeholder="e.g. 93300040"
            className="w-full"
          />
        </div>
        <div className="col-12 md:col-5">
          <label htmlFor="vc-pw" className="block font-medium mb-2">
            Password
          </label>
          <Password
            inputId="vc-pw"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            feedback={false}
            toggleMask
            className="w-full"
            inputClassName="w-full"
          />
        </div>
        <div className="col-12 md:col-2 flex align-items-end">
          <Button
            label="Validate"
            icon="pi pi-check"
            onClick={handleRun}
            loading={mutation.isPending}
          />
        </div>
      </div>
      <JsonResultBlock data={mutation.data} />
    </CollapsibleSection>
  );
};
