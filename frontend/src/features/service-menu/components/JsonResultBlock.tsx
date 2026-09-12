/**
 * Small reusable block that renders a JSON response with a "200 OK" tag.
 * Shared by service sections that just echo the raw response.
 */

import { Tag } from 'primereact/tag';

interface JsonResultBlockProps {
  data: unknown;
  label?: string;
}

export const JsonResultBlock = ({ data, label = 'Response' }: JsonResultBlockProps) => {
  if (!data) return null;
  return (
    <div className="mt-3 p-3 surface-100 border-round">
      <div className="flex align-items-center justify-content-between mb-2">
        <span className="font-semibold text-sm text-600">{label}</span>
        <Tag value="200 OK" severity="success" />
      </div>
      <pre className="text-xs overflow-auto m-0" style={{ maxHeight: '300px' }}>
        {JSON.stringify(data, null, 2)}
      </pre>
    </div>
  );
};
