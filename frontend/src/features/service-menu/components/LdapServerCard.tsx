/**
 * A single LDAP server card for the Services page.
 * Shows connectivity/health and provides a credential-validation form.
 */

import { useRef, useState } from 'react';

import { Button } from 'primereact/button';
import { InputText } from 'primereact/inputtext';
import { Password } from 'primereact/password';
import { Tag } from 'primereact/tag';
import { Toast } from 'primereact/toast';

import { extractApiError } from '@shared/utils/apiError';

import type { LdapConfig } from '../api/ldapApi';
import { useLdapHealth, useValidateLdapCredentials } from '../hooks/useLdap';

import { CollapsibleSection } from './CollapsibleSection';

interface LdapServerCardProps {
  config: LdapConfig;
  /** Initial collapsed state. Defaults to true (collapsed). */
  defaultCollapsed?: boolean;
}

const statusSeverity = (status: string | undefined) => {
  if (status === 'reachable') return 'success';
  if (status === 'unreachable' || status === 'auth_failed' || status === 'error') return 'danger';
  if (status === 'not_configured') return 'warning';
  return 'info';
};

export const LdapServerCard = ({ config, defaultCollapsed = true }: LdapServerCardProps) => {
  const toast = useRef<Toast>(null);

  const { data: health, isFetching, refetch } = useLdapHealth(config.id);
  const validateMutation = useValidateLdapCredentials();

  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');

  const handleValidate = async () => {
    if (!username.trim()) {
      toast.current?.show({
        severity: 'warn',
        summary: 'Validation',
        detail: 'Username is required',
        life: 3000,
      });
      return;
    }
    try {
      const result = await validateMutation.mutateAsync({
        id: config.id,
        request: { username: username.trim(), password },
      });
      toast.current?.show({
        severity: result.is_valid ? 'success' : 'warn',
        summary: 'Credential Validation',
        detail: result.message || (result.is_valid ? 'Valid user' : 'Invalid credentials'),
        life: 5000,
      });
    } catch (error) {
      toast.current?.show({
        severity: 'error',
        summary: 'Error',
        detail: extractApiError(error, 'Failed to validate credentials'),
        life: 5000,
      });
    }
  };

  const headerRight = (
    <div className="flex align-items-center gap-2">
      {!config.is_enabled && <Tag value="Disabled" severity="secondary" />}
      <Tag value={health?.status || 'unknown'} severity={statusSeverity(health?.status)} />
    </div>
  );

  return (
    <CollapsibleSection
      title={config.name}
      subTitle={config.server_uri}
      headerRight={headerRight}
      defaultCollapsed={defaultCollapsed}
    >
      <Toast ref={toast} />

      <div className="grid mb-2">
        <div className="col-12 md:col-8">
          <div className="flex flex-column gap-2">
            <div className="flex align-items-center gap-2">
              <span className="font-semibold text-600" style={{ minWidth: '110px' }}>
                Base DN:
              </span>
              <span className="text-sm">{config.base_dn || '-'}</span>
            </div>
            <div className="flex align-items-center gap-2">
              <span className="font-semibold text-600" style={{ minWidth: '110px' }}>
                Domain Prefix:
              </span>
              <span className="text-sm">{config.domain_prefix || '-'}</span>
            </div>
            <div className="flex align-items-center gap-2">
              <span className="font-semibold text-600" style={{ minWidth: '110px' }}>
                Configured:
              </span>
              <Tag
                value={health?.configured ? 'Yes' : 'No'}
                severity={health?.configured ? 'success' : 'warning'}
              />
            </div>
            {health?.error && (
              <div className="flex align-items-start gap-2">
                <span className="font-semibold text-600" style={{ minWidth: '110px' }}>
                  Error:
                </span>
                <span className="text-red-500 text-sm" style={{ wordBreak: 'break-all' }}>
                  {health.error}
                </span>
              </div>
            )}
          </div>
        </div>
        <div className="col-12 md:col-4 flex align-items-start justify-content-end">
          <Button
            label="Test Connection"
            icon="pi pi-refresh"
            severity="secondary"
            outlined
            loading={isFetching}
            onClick={() => refetch()}
            aria-label="Test connection"
          />
        </div>
      </div>

      <div className="surface-100 border-round p-3 mt-2">
        <div className="font-semibold text-700 mb-2">Validate User Credentials</div>
        <div className="grid">
          <div className="col-12 md:col-5">
            <label htmlFor={`u-${config.id}`} className="block text-sm font-medium mb-2">
              Username
            </label>
            <InputText
              id={`u-${config.id}`}
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="e.g. 93300116"
              className="w-full"
            />
          </div>
          <div className="col-12 md:col-5">
            <label htmlFor={`p-${config.id}`} className="block text-sm font-medium mb-2">
              Password
            </label>
            <Password
              inputId={`p-${config.id}`}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Enter password"
              className="w-full"
              inputClassName="w-full"
              feedback={false}
              toggleMask
            />
          </div>
          <div className="col-12 md:col-2 flex align-items-end">
            <Button
              label="Validate"
              icon="pi pi-check"
              onClick={handleValidate}
              loading={validateMutation.isPending}
              className="w-full"
            />
          </div>
        </div>
        {validateMutation.data && (
          <div className="mt-3">
            <div className="flex align-items-center gap-3 mb-2">
              <Tag
                value={validateMutation.data.is_valid ? 'Valid User' : 'Invalid User'}
                severity={validateMutation.data.is_valid ? 'success' : 'danger'}
                icon={validateMutation.data.is_valid ? 'pi pi-check' : 'pi pi-times'}
              />
              <span className="text-sm text-600">{validateMutation.data.message}</span>
            </div>
            {validateMutation.data.user_dn && (
              <div className="text-sm mb-2">
                <span className="font-semibold text-600">DN:</span> {validateMutation.data.user_dn}
              </div>
            )}
            {validateMutation.data.attributes &&
              Object.keys(validateMutation.data.attributes).length > 0 && (
                <pre className="text-xs overflow-auto m-0" style={{ maxHeight: '180px' }}>
                  {JSON.stringify(validateMutation.data.attributes, null, 2)}
                </pre>
              )}
          </div>
        )}
      </div>
    </CollapsibleSection>
  );
};
