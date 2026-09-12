/**
 * Reusable block that renders a raw text/XML response (as-is), for published
 * endpoints whose contract is not JSON (e.g. the <Response_To_Catalyst> XML
 * envelope). JSON responses should use JsonResultBlock instead.
 */

import { Tag } from 'primereact/tag';

interface RawResultBlockProps {
  data: string | null | undefined;
  label?: string;
  /** Small tag shown on the right, e.g. the content type. Defaults to "XML". */
  badge?: string;
}

export const RawResultBlock = ({ data, label = 'Response', badge = 'XML' }: RawResultBlockProps) => {
  if (!data) return null;
  return (
    <div className="mt-3 p-3 surface-100 border-round">
      <div className="flex align-items-center justify-content-between mb-2">
        <span className="font-semibold text-sm text-600">{label}</span>
        <Tag value={badge} severity="info" />
      </div>
      <pre className="text-xs overflow-auto m-0" style={{ maxHeight: '300px', whiteSpace: 'pre-wrap' }}>
        {data}
      </pre>
    </div>
  );
};
