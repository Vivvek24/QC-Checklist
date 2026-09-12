/**
 * Generic published E-Signer section for endpoints that take a single numeric
 * workflow id and return a JSON body (Get_Status, Download_Document,
 * GetAttachments, GetDocumentLogs, GetSignatureURL).
 *
 * The parent page owns the mutation (via its hook) and passes it in, along with
 * a `buildVars` mapper so each endpoint's param name (WorkFlowId / workflowId /
 * WorkflowID) is preserved.
 */

import { useState } from 'react';

import { Button } from 'primereact/button';
import { InputNumber } from 'primereact/inputnumber';
import type { ToastMessage } from 'primereact/toast';

import { CollapsibleSection } from '@features/service-menu/components/CollapsibleSection';
import { JsonResultBlock } from '@features/service-menu/components/JsonResultBlock';

import { extractApiError } from '@shared/utils/apiError';

/**
 * Generic over the mutation's variables type. Each endpoint's hook takes its own
 * shape (`WorkFlowId` vs `workflowId` vs `WorkflowID`), so a single concrete type
 * cannot describe them all — and widening `vars` to `Record<string, unknown>`
 * does not type check either, since a function accepting a narrow shape is not
 * assignable to one accepting a wider one. Threading `TVars` through instead ties
 * `buildVars`'s return type to `mutateAsync`'s parameter, and TypeScript infers it
 * per call site from the `buildVars` passed in.
 */
interface WorkflowMutation<TVars> {
  mutateAsync: (vars: TVars) => Promise<unknown>;
  isPending: boolean;
  data: unknown;
}

interface PublishedWorkflowNumberSectionProps<TVars> {
  title: string;
  subTitle: string;
  paramLabel: string;
  buttonLabel: string;
  buttonIcon: string;
  apiKey: string;
  notify: (message: ToastMessage) => void;
  mutation: WorkflowMutation<TVars>;
  buildVars: (apiKey: string, id: number) => TVars;
}

export const PublishedWorkflowNumberSection = <TVars,>({
  title,
  subTitle,
  paramLabel,
  buttonLabel,
  buttonIcon,
  apiKey,
  notify,
  mutation,
  buildVars,
}: PublishedWorkflowNumberSectionProps<TVars>) => {
  const [id, setId] = useState<number | null>(null);

  const handleRun = async () => {
    if (id == null) {
      notify({
        severity: 'warn',
        summary: 'Validation',
        detail: `Enter a ${paramLabel}`,
        life: 3000,
      });
      return;
    }
    try {
      await mutation.mutateAsync(buildVars(apiKey, id));
      notify({ severity: 'success', summary: 'Done', detail: 'Request completed', life: 3000 });
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
    <CollapsibleSection title={title} subTitle={subTitle}>
      <div className="grid">
        <div className="col-12 md:col-8">
          <label htmlFor={`wf-${title}`} className="block font-medium mb-2">
            {paramLabel}
          </label>
          <InputNumber
            inputId={`wf-${title}`}
            value={id}
            onValueChange={(e) => setId(e.value ?? null)}
            useGrouping={false}
            min={1}
            placeholder="e.g. 174810"
            className="w-full"
            inputClassName="w-full"
          />
        </div>
        <div className="col-12 md:col-4 flex align-items-end">
          <Button
            label={buttonLabel}
            icon={buttonIcon}
            onClick={handleRun}
            loading={mutation.isPending}
          />
        </div>
      </div>
      <JsonResultBlock data={mutation.data} />
    </CollapsibleSection>
  );
};
