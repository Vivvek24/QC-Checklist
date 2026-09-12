/**
 * Encryption Utility page (Services section).
 * A testing helper: type a plaintext value (an employee id or a password) and
 * get back the Fernet token to paste into a `validatecredentials` request. Uses
 * the same shared key as the backend's decrypt side, so the token round-trips.
 */

import { useRef, useState } from 'react';

import { Button } from 'primereact/button';
import { InputText } from 'primereact/inputtext';
import { Message } from 'primereact/message';
import { Tag } from 'primereact/tag';
import { Toast, type ToastMessage } from 'primereact/toast';

import { extractApiError } from '@shared/utils/apiError';

import { useEncrypt } from '../hooks/useEncryption';

export const EncryptionServicePage = () => {
  const toast = useRef<Toast>(null);
  const notify = (message: ToastMessage) => toast.current?.show(message);

  const [plaintext, setPlaintext] = useState('');
  const encryptMutation = useEncrypt();
  const result = encryptMutation.data;

  const handleEncrypt = async () => {
    const value = plaintext.trim();
    if (!value) {
      notify({
        severity: 'warn',
        summary: 'Nothing to encrypt',
        detail: 'Enter a value first.',
        life: 4000,
      });
      return;
    }
    try {
      await encryptMutation.mutateAsync(value);
    } catch (error) {
      notify({
        severity: 'error',
        summary: 'Error',
        detail: extractApiError(error, 'Failed to encrypt the value'),
        life: 5000,
      });
    }
  };

  const handleCopy = async () => {
    if (!result?.token) return;
    try {
      await navigator.clipboard.writeText(result.token);
      notify({
        severity: 'success',
        summary: 'Copied',
        detail: 'Token copied to clipboard.',
        life: 3000,
      });
    } catch {
      notify({
        severity: 'warn',
        summary: 'Copy failed',
        detail: 'Select the text and copy it manually.',
        life: 4000,
      });
    }
  };

  return (
    <div className="p-4">
      <Toast ref={toast} />

      <div className="mb-4">
        <h2 className="text-2xl font-semibold text-900 m-0">Encryption Utility</h2>
        <p className="text-600 mt-1 mb-0">
          Encrypt a value into the token used by the published validatecredentials endpoint
        </p>
      </div>

      <div className="surface-card p-4 border-round shadow-1" style={{ maxWidth: '640px' }}>
        <label htmlFor="plaintext" className="block text-900 font-medium mb-2">
          Plaintext value
        </label>
        <div className="flex gap-2">
          <InputText
            id="plaintext"
            value={plaintext}
            onChange={(e) => setPlaintext(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter') handleEncrypt();
            }}
            placeholder="e.g. an employee id or a password"
            className="flex-1"
            autoComplete="off"
          />
          <Button
            label="Encrypt"
            icon="pi pi-lock"
            onClick={handleEncrypt}
            loading={encryptMutation.isPending}
          />
        </div>
        <small className="text-600 block mt-2">
          Paste the result into the EmployeeId or Password field of a validatecredentials request.
        </small>

        {result && (
          <div className="mt-4 p-3 surface-100 border-round">
            <div className="flex align-items-center gap-2 mb-2">
              <span className="text-900 font-medium">Encrypted token</span>
              <Tag
                value={result.encrypted ? 'Encrypted' : 'Passthrough (plaintext)'}
                severity={result.encrypted ? 'success' : 'warning'}
                icon={result.encrypted ? 'pi pi-lock' : 'pi pi-unlock'}
              />
            </div>
            {!result.encrypted && (
              <Message
                severity="warn"
                className="w-full justify-content-start mb-2"
                text="No encryption key is configured on the server, so the value was returned unchanged."
              />
            )}
            <div className="flex gap-2 align-items-start">
              <InputText
                value={result.token}
                readOnly
                className="flex-1 font-mono text-sm"
                onFocus={(e) => e.target.select()}
              />
              <Button
                icon="pi pi-copy"
                severity="secondary"
                outlined
                onClick={handleCopy}
                tooltip="Copy to clipboard"
                tooltipOptions={{ position: 'top' }}
                aria-label="Copy token"
              />
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
