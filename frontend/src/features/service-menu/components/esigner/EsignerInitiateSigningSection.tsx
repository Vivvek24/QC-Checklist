/**
 * E-Signer — InitiateEmbeddedSigning section.
 * Logs in for an access token, then starts a signing session with a JSON body.
 */

import { useState } from 'react';

import { Button } from 'primereact/button';
import { InputTextarea } from 'primereact/inputtextarea';
import { Tag } from 'primereact/tag';

import { extractApiError } from '@shared/utils/apiError';

import { useEsignerInitiateSigning } from '../../hooks/useEsigner';
import { CollapsibleSection } from '../CollapsibleSection';
import type { ServiceSectionProps } from '../sectionProps';

export const EsignerInitiateSigningSection = ({ notify }: ServiceSectionProps) => {
  const [signingBody, setSigningBody] = useState('{\n  \n}');
  const initiateSigningMutation = useEsignerInitiateSigning();

  const handleInitiateSigning = async () => {
    let parsed: Record<string, unknown>;
    try {
      parsed = JSON.parse(signingBody);
    } catch {
      notify({
        severity: 'warn',
        summary: 'Invalid JSON',
        detail: 'The request body is not valid JSON.',
        life: 4000,
      });
      return;
    }
    try {
      const result = await initiateSigningMutation.mutateAsync(parsed);
      notify({
        severity: result.IsSuccess ? 'success' : 'warn',
        summary: 'Embedded Signing',
        detail:
          result.Messages?.filter(Boolean).join(' ') ||
          (result.IsSuccess ? 'Signing session created' : 'Failed to create session'),
        life: 5000,
      });
    } catch (error) {
      notify({
        severity: 'error',
        summary: 'Error',
        detail: extractApiError(error, 'Failed to initiate embedded signing'),
        life: 5000,
      });
    }
  };

  return (
    <CollapsibleSection
      title="POST /initiate-embedded-signing"
      subTitle="Logs in for an access token, then starts an embedded signing session with the JSON body below."
    >
      <label htmlFor="signing-body" className="block font-medium mb-2">
        Request body (JSON)
      </label>
      <InputTextarea
        id="signing-body"
        value={signingBody}
        onChange={(e) => setSigningBody(e.target.value)}
        rows={10}
        className="w-full font-mono"
        style={{ fontSize: '0.8rem' }}
        spellCheck={false}
        placeholder='{ "DocumentDetails": [ ... ] }'
      />
      <div className="flex align-items-center gap-3 mt-3">
        <Button
          label="Initiate Signing"
          icon="pi pi-file-edit"
          onClick={handleInitiateSigning}
          loading={initiateSigningMutation.isPending}
        />
      </div>
      {initiateSigningMutation.data && (
        <div className="mt-3 p-3 surface-100 border-round">
          <div className="flex align-items-center gap-3 mb-2 flex-wrap">
            <Tag
              value={initiateSigningMutation.data.IsSuccess ? 'Success' : 'Failed'}
              severity={initiateSigningMutation.data.IsSuccess ? 'success' : 'danger'}
              icon={initiateSigningMutation.data.IsSuccess ? 'pi pi-check' : 'pi pi-times'}
            />
            {initiateSigningMutation.data.Messages?.filter(Boolean).map((m, i) => (
              <span key={i} className="text-sm text-700">
                {m}
              </span>
            ))}
          </div>
          {initiateSigningMutation.data.Response?.URL && (
            <div className="mb-2">
              <a
                href={initiateSigningMutation.data.Response.URL}
                target="_blank"
                rel="noopener noreferrer"
                className="text-primary text-sm"
                style={{ wordBreak: 'break-all' }}
              >
                <i className="pi pi-external-link mr-1" />
                Open signing URL
              </a>
            </div>
          )}
          <pre className="text-xs overflow-auto m-0" style={{ maxHeight: '300px' }}>
            {JSON.stringify(initiateSigningMutation.data, null, 2)}
          </pre>
        </div>
      )}
    </CollapsibleSection>
  );
};
