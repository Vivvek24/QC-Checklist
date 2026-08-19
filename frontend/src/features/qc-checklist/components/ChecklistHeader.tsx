/**
 * ChecklistHeader — reusable header component for QC Checklist pages.
 * All info inside the gradient ribbon strip.
 * Left: Company + location. Center: Format name. Right: Format no.
 * Styles in theme-overrides.css (.qc-header-*).
 */

interface Props {
  companyName?: string;
  unitName?: string;
  formatName: string;
  formatNo: string;
}

export const ChecklistHeader = ({ companyName = 'EMCURE', unitName = '', formatName, formatNo }: Props) => {
  return (
    <div className="qc-header">
      <div className="qc-header-ribbon-wrap">
        <div className="qc-header-ribbon">
          {/* Left — Company + Location */}
          <div className="qc-header-ribbon-left">
            <div className="qc-header-company">{companyName}</div>
            <div className="qc-header-location">
              <i className="pi pi-map-marker" />
              <span>{unitName}</span>
            </div>
          </div>

          {/* Center — Format name */}
          <div className="qc-header-ribbon-center">
            <span className="qc-header-format-name">{formatName}</span>
          </div>

          {/* Right — Format number */}
          <div className="qc-header-ribbon-right">
            <span className="qc-header-format-no">{formatNo}</span>
          </div>
        </div>
      </div>
    </div>
  );
};
