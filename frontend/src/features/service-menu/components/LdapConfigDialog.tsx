/**
 * Create/Edit dialog for an LDAP server configuration.
 */

import { useEffect, useState } from 'react';

import { Button } from 'primereact/button';
import { Dialog } from 'primereact/dialog';
import { InputSwitch } from 'primereact/inputswitch';
import { InputText } from 'primereact/inputtext';
import { Password } from 'primereact/password';

import type { LdapConfig, LdapConfigCreateRequest } from '../api/ldapApi';

interface LdapConfigDialogProps {
  visible: boolean;
  /** When provided, the dialog is in edit mode. */
  config?: LdapConfig | null;
  loading?: boolean;
  onHide: () => void;
  onSubmit: (form: LdapConfigCreateRequest) => void;
}

const EMPTY_FORM: LdapConfigCreateRequest = {
  name: '',
  server_uri: '',
  base_dn: '',
  bind_username: '',
  bind_password: '',
  domain_prefix: '',
  use_ssl: false,
  is_enabled: true,
};

export const LdapConfigDialog = ({
  visible,
  config,
  loading,
  onHide,
  onSubmit,
}: LdapConfigDialogProps) => {
  const isEdit = !!config;
  const [form, setForm] = useState<LdapConfigCreateRequest>(EMPTY_FORM);

  useEffect(() => {
    if (visible) {
      if (config) {
        setForm({
          name: config.name,
          server_uri: config.server_uri,
          base_dn: config.base_dn,
          bind_username: config.bind_username,
          bind_password: '',
          domain_prefix: config.domain_prefix,
          use_ssl: config.use_ssl,
          is_enabled: config.is_enabled,
        });
      } else {
        setForm(EMPTY_FORM);
      }
    }
  }, [visible, config]);

  const setField = <K extends keyof LdapConfigCreateRequest>(
    key: K,
    value: LdapConfigCreateRequest[K],
  ) => setForm((prev) => ({ ...prev, [key]: value }));

  const passwordSet = config?.bind_password_set ?? false;

  const footer = (
    <div className="flex justify-content-end gap-2">
      <Button
        label="Cancel"
        icon="pi pi-times"
        outlined
        severity="secondary"
        onClick={onHide}
        disabled={loading}
      />
      <Button
        label={isEdit ? 'Save Changes' : 'Create'}
        icon="pi pi-check"
        onClick={() => onSubmit(form)}
        loading={loading}
      />
    </div>
  );

  return (
    <Dialog
      header={isEdit ? `Edit LDAP Server — ${config?.name}` : 'New LDAP Server'}
      visible={visible}
      onHide={onHide}
      style={{ width: '640px' }}
      modal
      footer={footer}
    >
      <div className="grid formgrid p-fluid pt-2">
        <div className="field col-12 md:col-6">
          <label htmlFor="cfg-name" className="block font-medium mb-2">
            Name
          </label>
          <InputText
            id="cfg-name"
            value={form.name}
            onChange={(e) => setField('name', e.target.value)}
            placeholder="Emcure Pharma"
          />
        </div>
        <div className="field col-12 md:col-6">
          <label htmlFor="cfg-server" className="block font-medium mb-2">
            Server URI
          </label>
          <InputText
            id="cfg-server"
            value={form.server_uri}
            onChange={(e) => setField('server_uri', e.target.value)}
            placeholder="ldap://10.21.91.59:389"
          />
        </div>
        <div className="field col-12 md:col-6">
          <label htmlFor="cfg-basedn" className="block font-medium mb-2">
            Base DN (Root Directory)
          </label>
          <InputText
            id="cfg-basedn"
            value={form.base_dn}
            onChange={(e) => setField('base_dn', e.target.value)}
            placeholder="DC=emcure,DC=pharma"
          />
        </div>
        <div className="field col-12 md:col-6">
          <label htmlFor="cfg-domain" className="block font-medium mb-2">
            Domain Prefix
          </label>
          <InputText
            id="cfg-domain"
            value={form.domain_prefix}
            onChange={(e) => setField('domain_prefix', e.target.value)}
            placeholder="EPLPHARMA\"
          />
        </div>
        <div className="field col-12 md:col-6">
          <label htmlFor="cfg-binduser" className="block font-medium mb-2">
            Bind Username (System Account)
          </label>
          {/* Escaped backslash: a bare "\9" reads as a nonoctal decimal escape. */}
          <InputText
            id="cfg-binduser"
            value={form.bind_username}
            onChange={(e) => setField('bind_username', e.target.value)}
            placeholder={'EPLPHARMA\\93300116'}
          />
        </div>
        <div className="field col-12 md:col-6">
          <label htmlFor="cfg-bindpass" className="block font-medium mb-2">
            Bind Password{' '}
            {isEdit && passwordSet && (
              <span className="text-500 text-sm font-normal">(leave blank to keep current)</span>
            )}
          </label>
          <Password
            id="cfg-bindpass"
            value={form.bind_password}
            onChange={(e) => setField('bind_password', e.target.value)}
            placeholder={isEdit && passwordSet ? '••••••••' : 'Enter password'}
            feedback={false}
            toggleMask
          />
        </div>
        <div className="field col-6 md:col-3 flex flex-column">
          <label htmlFor="cfg-ssl" className="block font-medium mb-2">
            Use SSL (LDAPS)
          </label>
          <InputSwitch
            id="cfg-ssl"
            checked={form.use_ssl}
            onChange={(e) => setField('use_ssl', !!e.value)}
          />
        </div>
        <div className="field col-6 md:col-3 flex flex-column">
          <label htmlFor="cfg-enabled" className="block font-medium mb-2">
            Enabled
          </label>
          <InputSwitch
            id="cfg-enabled"
            checked={form.is_enabled}
            onChange={(e) => setField('is_enabled', !!e.value)}
          />
        </div>
      </div>
    </Dialog>
  );
};
