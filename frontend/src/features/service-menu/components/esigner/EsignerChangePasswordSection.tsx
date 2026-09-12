/**
 * E-Signer — ChangePassword (rotation) section.
 * Rotates the account password to the temp value and back.
 */

import { Button } from 'primereact/button';
import { Tag } from 'primereact/tag';

import { extractApiError } from '@shared/utils/apiError';

import { useEsignerChangePassword } from '../../hooks/useEsigner';
import { CollapsibleSection } from '../CollapsibleSection';
import type { ServiceSectionProps } from '../sectionProps';

export const EsignerChangePasswordSection = ({ notify }: ServiceSectionProps) => {
  const changePasswordMutation = useEsignerChangePassword();

  const handleChangePassword = async () => {
    try {
      const result = await changePasswordMutation.mutateAsync();
      notify({
        severity: result.IsSuccess ? 'success' : 'warn',
        summary: 'E-Signer Password Rotation',
        detail: result.message || (result.IsSuccess ? 'Password rotated' : 'Rotation failed'),
        life: 6000,
      });
    } catch (error) {
      notify({
        severity: 'error',
        summary: 'Error',
        detail: extractApiError(error, 'Failed to rotate E-Signer password'),
        life: 5000,
      });
    }
  };

  return (
    <CollapsibleSection
      title="POST /change-password"
      subTitle="Rotate the account password (change to the temporary password and back) to satisfy expiry policies without affecting other apps."
    >
      <div className="flex align-items-center gap-3">
        <Button
          label="Rotate Password"
          icon="pi pi-sync"
          severity="warning"
          onClick={handleChangePassword}
          loading={changePasswordMutation.isPending}
        />
        <span className="text-600 text-sm">
          Changes to ESIGNER_TEMP_PASSWORD, then restores ESIGNER_PASSWORD.
        </span>
      </div>
      {changePasswordMutation.data && (
        <div className="mt-3 p-3 surface-100 border-round">
          <div className="flex align-items-center gap-3 mb-2">
            <Tag
              value={changePasswordMutation.data.IsSuccess ? 'Success' : 'Failed'}
              severity={changePasswordMutation.data.IsSuccess ? 'success' : 'danger'}
              icon={changePasswordMutation.data.IsSuccess ? 'pi pi-check' : 'pi pi-times'}
            />
            <span className="text-sm text-700">{changePasswordMutation.data.message}</span>
          </div>
          <pre className="text-xs overflow-auto m-0" style={{ maxHeight: '260px' }}>
            {JSON.stringify(changePasswordMutation.data, null, 2)}
          </pre>
        </div>
      )}
    </CollapsibleSection>
  );
};
