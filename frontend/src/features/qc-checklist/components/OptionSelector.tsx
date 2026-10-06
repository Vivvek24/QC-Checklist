/**
 * OptionSelector — reusable component for Select Options column.
 * Renders Dropdown (single select) or MultiSelect based on answer_type.
 * Shows N/A for other answer types.
 */

import { Dropdown } from 'primereact/dropdown';
import { MultiSelect } from 'primereact/multiselect';

interface Props {
  answerType: string;
  options: { id: number; label: string }[];
  value: any;
  onChange: (value: any) => void;
  disabled?: boolean;
}

export const OptionSelector = ({ answerType, options, value, onChange, disabled = false }: Props) => {
  const opts = options.map((o) => ({ label: o.label, value: o.id }));

  if (answerType === 'Dropdown (multi select)') {
    // MultiSelect requires an array value (it calls .slice internally).
    // Coerce a stray scalar/null to a safe array so it can never crash.
    const multiValue = Array.isArray(value) ? value : value == null ? [] : [value];
    return (
      <MultiSelect value={multiValue} placeholder="" className="w-full" options={opts} filter
        display="chip" onChange={(e) => onChange(e.value)} disabled={disabled}
        style={{ minHeight: '1.85rem', fontSize: '0.75rem' }} />
    );
  }

  if (answerType === 'Dropdown (single select)') {
    return (
      <Dropdown value={value || null} placeholder="" className="w-full" options={opts} filter
        showClear disabled={disabled}
        onChange={(e) => onChange(e.value)}
        style={{ height: '1.85rem', fontSize: '0.75rem' }} />
    );
  }

  return <span style={{ color: '#94a3b8', fontSize: '0.78rem' }}>N/A</span>;
};
