/**
 * E-Signer — ValidateLogin section.
 * Authenticates using the credentials configured in the backend .env.
 */

import { Button } from 'primereact/button';
import { Tag } from 'primereact/tag';

import { extractApiError } from '@shared/utils/apiError';

import { useEsignerLogin } from '../../hooks/useEsigner';
import { CollapsibleSection } from '../CollapsibleSection';
import type { ServiceSectionProps } from '../sectionProps';

export const EsignerLoginSection = ({ notify }: ServiceSectionProps) => {
  const loginMutation = useEsignerLogin();

  const handleLogin = async () => {
    try {
      const result = await loginMutation.mutateAsync();
      notify({
        severity: result.IsSuccess ? 'success' : 'warn',
        summary: 'E-Signer Login',
        detail: result.IsSuccess
          ? 'Authenticated successfully'
          : result.Messages?.filter(Boolean).join(' ') || 'Login failed',
        life: 5000,
      });
    } catch (error) {
      notify({
        severity: 'error',
        summary: 'Error',
        detail: extractApiError(error, 'Failed to call E-Signer login'),
        life: 5000,
      });
    }
  };

  return (
    <CollapsibleSection
      title="POST /login"
      subTitle="Authenticate against E-Signer (ValidateLogin) using the configured account credentials."
    >
      <div className="flex align-items-center gap-3">
        <Button
          label="Login"
          icon="pi pi-sign-in"
          onClick={handleLogin}
          loading={loginMutation.isPending}
        />
        <span className="text-600 text-sm">
          Uses the E-Signer account configured in the backend environment.
        </span>
      </div>
      {loginMutation.data && (
        <div className="mt-3 p-3 surface-100 border-round">
          <div className="flex align-items-center gap-3 mb-2">
            <Tag
              value={loginMutation.data.IsSuccess ? 'Success' : 'Failed'}
              severity={loginMutation.data.IsSuccess ? 'success' : 'danger'}
              icon={loginMutation.data.IsSuccess ? 'pi pi-check' : 'pi pi-times'}
            />
            {loginMutation.data.Response?.AuthToken && (
              <Tag value="Auth token received" severity="info" icon="pi pi-key" />
            )}
          </div>
          <pre className="text-xs overflow-auto m-0" style={{ maxHeight: '260px' }}>
            {JSON.stringify(loginMutation.data, null, 2)}
          </pre>
        </div>
      )}
    </CollapsibleSection>
  );
};
