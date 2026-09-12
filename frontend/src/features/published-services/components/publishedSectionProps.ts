/**
 * Shared props for published-service endpoint section components.
 *
 * Like the internal service sections, the parent page owns a single Toast and
 * passes a `notify` helper down. In addition, published sections receive the
 * current `apiKey` (from the page-level input) so each call can send the
 * optional `X-API-Key` header exactly as an external caller would.
 */

import type { ToastMessage } from 'primereact/toast';

export interface PublishedSectionProps {
  notify: (message: ToastMessage) => void;
  apiKey: string;
}
