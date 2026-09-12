/**
 * Shared props for service endpoint section components.
 * The parent page owns a single Toast and passes a `notify` helper down so
 * every section can surface feedback through the same toast.
 */

import type { ToastMessage } from 'primereact/toast';

export interface ServiceSectionProps {
  notify: (message: ToastMessage) => void;
}
