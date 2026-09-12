/**
 * Collapsible section for service pages.
 * Wraps a PrimeReact Panel so each endpoint's controls can be grouped and
 * collapsed. Collapsed by default to keep long service pages compact.
 */

import { useState, type ReactNode } from 'react';

import { Panel } from 'primereact/panel';

interface CollapsibleSectionProps {
  title: string;
  subTitle?: string;
  /** Initial collapsed state. Defaults to true (collapsed). */
  defaultCollapsed?: boolean;
  /** Optional node rendered on the right side of the header (e.g. a status tag). */
  headerRight?: ReactNode;
  children: ReactNode;
}

export const CollapsibleSection = ({
  title,
  subTitle,
  defaultCollapsed = true,
  headerRight,
  children,
}: CollapsibleSectionProps) => {
  const [collapsed, setCollapsed] = useState(defaultCollapsed);

  const header = (
    <div className="flex align-items-center justify-content-between w-full gap-3">
      <div className="flex flex-column">
        <span className="font-semibold text-900">{title}</span>
        {subTitle && <span className="text-600 text-sm font-normal mt-1">{subTitle}</span>}
      </div>
      {headerRight}
    </div>
  );

  return (
    <Panel
      header={header}
      toggleable
      collapsed={collapsed}
      onToggle={(e) => setCollapsed(e.value)}
      className="mb-3"
    >
      {children}
    </Panel>
  );
};
