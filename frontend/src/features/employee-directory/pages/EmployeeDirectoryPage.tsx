/**
 * Employee Directory page (Main section).
 * Lists all employees (active + inactive) stored locally, with search and
 * status filtering, plus the ability to fetch active/inactive employees from
 * Darwinbox on demand.
 *
 * The grid exposes every employee attribute (excluding the audit fields
 * created/modified by/date) and lets the user show/hide columns via a
 * MultiSelect toggle.
 */

import { useState, useEffect, useRef, type ReactNode } from 'react';

import { Button } from 'primereact/button';
import { Card } from 'primereact/card';
import { Column } from 'primereact/column';
import { DataTable } from 'primereact/datatable';
import { Dialog } from 'primereact/dialog';
import { Dropdown } from 'primereact/dropdown';
import { InputText } from 'primereact/inputtext';
import { MultiSelect } from 'primereact/multiselect';
import { ProgressSpinner } from 'primereact/progressspinner';
import { Tag } from 'primereact/tag';
import { Toast } from 'primereact/toast';

import type {
  DarwinboxEmployee,
  DarwinboxSyncScope,
} from '@features/service-menu/api/darwinboxApi';
import { useDarwinboxStored, useSyncDarwinbox } from '@features/service-menu/hooks/useDarwinbox';

import { extractApiError } from '@shared/utils/apiError';

const STATUS_FILTERS: { label: string; value: string | null }[] = [
  { label: 'All', value: null },
  { label: 'Active', value: 'Active' },
  { label: 'Inactive', value: 'Inactive' },
];

const statusTemplate = (row: DarwinboxEmployee): ReactNode => (
  <Tag
    value={row.employee_status || '-'}
    severity={row.employee_status?.toLowerCase() === 'active' ? 'success' : 'warning'}
  />
);

interface ColumnDef {
  field: keyof DarwinboxEmployee;
  header: string;
  minWidth: string;
  body?: (row: DarwinboxEmployee) => ReactNode;
}

/**
 * Every employee attribute we expose in the grid, excluding the audit fields
 * (created_by, created_date, modified_by, modified_date).
 */
const COLUMN_DEFS: ColumnDef[] = [
  { field: 'employee_id', header: 'Emp ID', minWidth: '100px' },
  { field: 'full_name', header: 'Name', minWidth: '170px' },
  { field: 'first_name', header: 'First Name', minWidth: '140px' },
  { field: 'middle_name', header: 'Middle Name', minWidth: '140px' },
  { field: 'last_name', header: 'Last Name', minWidth: '140px' },
  { field: 'company_email_id', header: 'Email', minWidth: '240px' },
  { field: 'employee_status', header: 'Status', minWidth: '110px', body: statusTemplate },
  { field: 'designation_title', header: 'Designation', minWidth: '180px' },
  { field: 'job_level', header: 'Job Level', minWidth: '160px' },
  { field: 'role', header: 'Role', minWidth: '160px' },
  { field: 'department', header: 'Department', minWidth: '180px' },
  { field: 'business_unit', header: 'Business Unit', minWidth: '160px' },
  { field: 'division', header: 'Division', minWidth: '150px' },
  { field: 'group_company', header: 'Group Company', minWidth: '170px' },
  { field: 'catalyst_additional_department', header: 'Additional Department', minWidth: '190px' },
  { field: 'departments_hierarchy', header: 'Department Hierarchy', minWidth: '200px' },
  { field: 'cost_center_id', header: 'Cost Center ID', minWidth: '140px' },
  { field: 'cost_center', header: 'Cost Center', minWidth: '160px' },
  { field: 'office_mobile_no', header: 'Office Mobile', minWidth: '140px' },
  { field: 'extension_mobile_no', header: 'Extension', minWidth: '120px' },
  { field: 'personal_mobile_no', header: 'Personal Mobile', minWidth: '150px' },
  { field: 'current_address', header: 'Current Address', minWidth: '240px' },
  { field: 'current_country', header: 'Country', minWidth: '130px' },
  { field: 'current_location', header: 'Current Location', minWidth: '170px' },
  { field: 'office_location', header: 'Office Location', minWidth: '170px' },
  { field: 'custom_location', header: 'Custom Location', minWidth: '160px' },
  { field: 'office_state', header: 'State', minWidth: '130px' },
  { field: 'office_city', header: 'City', minWidth: '130px' },
  { field: 'direct_manager_employee_id', header: 'Manager ID', minWidth: '120px' },
  { field: 'direct_manager_name', header: 'Manager', minWidth: '170px' },
  { field: 'direct_manager_email', header: 'Manager Email', minWidth: '240px' },
  { field: 'territory_code', header: 'Territory Code', minWidth: '140px' },
  { field: 'territory_name', header: 'Territory Name', minWidth: '160px' },
  { field: 'bank_pan', header: 'PAN', minWidth: '120px' },
  { field: 'date_of_birth', header: 'DOB', minWidth: '120px' },
  { field: 'gender', header: 'Gender', minWidth: '110px' },
  { field: 'date_of_exit', header: 'Exit Date', minWidth: '120px' },
];

const COLUMN_OPTIONS = COLUMN_DEFS.map((c) => ({ label: c.header, value: c.field }));

// Sensible default set so the grid isn't overwhelming on first load.
const DEFAULT_FIELDS: (keyof DarwinboxEmployee)[] = [
  'employee_id',
  'full_name',
  'company_email_id',
  'employee_status',
  'designation_title',
  'department',
  'business_unit',
  'office_location',
  'direct_manager_name',
  'date_of_exit',
];

export const EmployeeDirectoryPage = () => {
  const toast = useRef<Toast>(null);

  // Filters & pagination
  const [statusFilter, setStatusFilter] = useState<string | null>(null);
  const [searchInput, setSearchInput] = useState('');
  const [search, setSearch] = useState('');
  const [rows, setRows] = useState(25);
  const [first, setFirst] = useState(0);

  // Visible columns (show/hide)
  const [visibleFields, setVisibleFields] = useState<(keyof DarwinboxEmployee)[]>(DEFAULT_FIELDS);

  // Debounce the search input so we don't query on every keystroke
  useEffect(() => {
    const handle = setTimeout(() => {
      setSearch(searchInput.trim());
      setFirst(0);
    }, 400);
    return () => clearTimeout(handle);
  }, [searchInput]);

  const { data, isLoading, isFetching } = useDarwinboxStored({
    skip: first,
    limit: rows,
    status: statusFilter ?? undefined,
    search: search || undefined,
  });

  const syncMutation = useSyncDarwinbox();

  const handleFetch = async (scope: DarwinboxSyncScope) => {
    try {
      const result = await syncMutation.mutateAsync(scope);
      toast.current?.show({
        severity: 'success',
        summary: 'Fetch complete',
        detail: `${scope} • total ${result.total} • created ${result.created} • updated ${result.updated} • failed ${result.failed}`,
        life: 6000,
      });
    } catch (error) {
      toast.current?.show({
        severity: 'error',
        summary: 'Fetch failed',
        detail: extractApiError(error, 'Failed to fetch employees'),
        life: 6000,
      });
    }
  };

  // Preserve the configured column order regardless of selection order.
  const orderedVisible = COLUMN_DEFS.filter((c) => visibleFields.includes(c.field));

  // Paginator "showing X - Y of Z" label (comma-formatted).
  const totalRecords = data?.total ?? 0;
  const rangeStart = totalRecords === 0 ? 0 : first + 1;
  const rangeEnd = Math.min(first + rows, totalRecords);
  const rangeLabel = `${rangeStart.toLocaleString()} - ${rangeEnd.toLocaleString()} of ${totalRecords.toLocaleString()}`;

  const columnToggle = (
    <MultiSelect
      value={visibleFields}
      options={COLUMN_OPTIONS}
      onChange={(e) => {
        // Keep at least one column visible.
        setVisibleFields(e.value.length ? e.value : DEFAULT_FIELDS);
      }}
      filter
      filterPlaceholder="Find column"
      placeholder="Columns"
      selectedItemsLabel="{0} columns shown"
      maxSelectedLabels={0}
      dropdownIcon="pi pi-sliders-h"
      className="w-14rem"
      panelClassName="text-sm"
    />
  );

  return (
    <div className="p-4">
      <Toast ref={toast} />

      {/* Blocking overlay while a fetch/sync runs */}
      <Dialog
        visible={syncMutation.isPending}
        modal
        closable={false}
        draggable={false}
        resizable={false}
        showHeader={false}
        onHide={() => {}}
        style={{ width: '420px' }}
      >
        <div className="flex flex-column align-items-center gap-3 py-4 text-center">
          <ProgressSpinner style={{ width: '48px', height: '48px' }} strokeWidth="4" />
          <span className="font-semibold text-900">Fetching employees</span>
          <span className="text-600 text-sm">
            Fetching from Darwinbox. This can take a few minutes for the full dataset (~16k
            records). Please keep this tab open.
          </span>
        </div>
      </Dialog>

      {/* Header */}
      <div className="flex align-items-center justify-content-between mb-4 flex-wrap gap-3">
        <div>
          <h2 className="text-2xl font-semibold text-900 m-0">Employees</h2>
          <p className="text-600 mt-1 mb-0">
            Directory of all employees (active and inactive) synced from Darwinbox
          </p>
        </div>
        <div className="flex gap-2">
          <Button
            label="Fetch Active"
            icon="pi pi-user-plus"
            onClick={() => handleFetch('active')}
            loading={syncMutation.isPending}
          />
          <Button
            label="Fetch Inactive"
            icon="pi pi-user-minus"
            severity="secondary"
            onClick={() => handleFetch('inactive')}
            loading={syncMutation.isPending}
          />
          <Button
            label="Fetch All"
            icon="pi pi-sync"
            severity="help"
            outlined
            onClick={() => handleFetch('all')}
            loading={syncMutation.isPending}
          />
        </div>
      </div>

      <Card>
        {/* Toolbar: search + column toggle + status filter */}
        <div className="flex align-items-center justify-content-between mb-3 flex-wrap gap-3">
          <span className="relative inline-flex align-items-center">
            <i
              className="pi pi-search"
              style={{
                position: 'absolute',
                left: '0.75rem',
                color: 'var(--text-color-secondary)',
                pointerEvents: 'none',
              }}
            />
            <InputText
              value={searchInput}
              onChange={(e) => setSearchInput(e.target.value)}
              placeholder="Search id, name, email, department"
              className="w-20rem"
              style={{ paddingLeft: '2.5rem' }}
            />
          </span>
          <div className="flex align-items-center gap-3 flex-wrap">
            <span className="text-500 text-sm white-space-nowrap">
              {(data?.total ?? 0).toLocaleString()} employee{(data?.total ?? 0) === 1 ? '' : 's'}
            </span>
            {columnToggle}
            <Dropdown
              value={statusFilter}
              options={STATUS_FILTERS}
              onChange={(e) => {
                setStatusFilter(e.value);
                setFirst(0);
              }}
              placeholder="All statuses"
              className="w-10rem"
            />
          </div>
        </div>

        <DataTable
          value={data?.employees ?? []}
          loading={isLoading || isFetching}
          lazy
          paginator
          rows={rows}
          first={first}
          totalRecords={totalRecords}
          onPage={(e) => {
            setFirst(e.first);
            setRows(e.rows);
          }}
          rowsPerPageOptions={[10, 25, 50, 100]}
          paginatorTemplate="FirstPageLink PrevPageLink PageLinks NextPageLink LastPageLink RowsPerPageDropdown"
          paginatorLeft={<span className="text-500 text-sm white-space-nowrap">{rangeLabel}</span>}
          paginatorClassName="justify-content-between align-items-center border-top-1 surface-border"
          size="small"
          stripedRows
          scrollable
          emptyMessage="No employees found. Use Fetch Active / Fetch Inactive to populate."
        >
          {orderedVisible.map((col) => (
            <Column
              key={col.field}
              field={col.field}
              header={col.header}
              body={col.body}
              style={{ minWidth: col.minWidth }}
            />
          ))}
        </DataTable>
      </Card>
    </div>
  );
};
