/**
 * Published E-Signer — POST /Login_and_Send_Document section.
 *
 * Sends a JSON InitiateEmbeddedSigning body and renders the raw
 * <Response_To_Catalyst> XML envelope returned by the endpoint.
 */

import { useState } from 'react';

import { Button } from 'primereact/button';
import { InputTextarea } from 'primereact/inputtextarea';

import { CollapsibleSection } from '@features/service-menu/components/CollapsibleSection';

import { extractApiError } from '@shared/utils/apiError';

import { usePublishedLoginAndSend } from '../../hooks/usePublishedEsigner';
import type { PublishedSectionProps } from '../publishedSectionProps';
import { RawResultBlock } from '../RawResultBlock';

export const PublishedLoginAndSendSection = ({ notify, apiKey }: PublishedSectionProps) => {
  const [body, setBody] = useState('{\n  \n}');
  const mutation = usePublishedLoginAndSend();

  const handleRun = async () => {
    let parsed: Record<string, unknown>;
    try {
      parsed = JSON.parse(body);
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
      await mutation.mutateAsync({ apiKey, body: parsed });
      notify({
        severity: 'success',
        summary: 'Done',
        detail: 'Request completed (see XML response)',
        life: 3000,
      });
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
      title="POST /Login_and_Send_Document"
      subTitle="Logs in and initiates embedded signing; returns the <Response_To_Catalyst> XML envelope."
    >
      <label htmlFor="las-body" className="block font-medium mb-2">
        Request body (JSON)
      </label>
      <InputTextarea
        id="las-body"
        value={body}
        onChange={(e) => setBody(e.target.value)}
        rows={10}
        className="w-full font-mono"
        style={{ fontSize: '0.8rem' }}
        spellCheck={false}
        placeholder='{ "DocumentDetails": [ ... ] }'
      />
      <div className="flex align-items-center gap-3 mt-3">
        <Button
          label="Login & Send"
          icon="pi pi-send"
          onClick={handleRun}
          loading={mutation.isPending}
        />
      </div>
      <RawResultBlock data={mutation.data} label="Response (XML)" badge="XML" />
    </CollapsibleSection>
  );
};
