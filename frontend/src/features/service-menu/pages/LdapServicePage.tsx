/**
 * LDAP Service page (Services section).
 * Lists all configured LDAP servers with per-server health status and a
 * credential-validation form.
 */

import { Message } from 'primereact/message';
import { ProgressSpinner } from 'primereact/progressspinner';

import { LdapServerCard } from '../components/LdapServerCard';
import { useLdapConfigs } from '../hooks/useLdap';

export const LdapServicePage = () => {
  const { data, isLoading } = useLdapConfigs();
  const configs = data?.configs ?? [];

  return (
    <div className="p-4">
      <div className="mb-4">
        <h2 className="text-2xl font-semibold text-900 m-0">LDAP</h2>
        <p className="text-600 mt-1 mb-0">
          Check connectivity and validate user credentials against configured LDAP servers
        </p>
      </div>

      {isLoading ? (
        <div className="flex align-items-center gap-2">
          <ProgressSpinner style={{ width: '24px', height: '24px' }} />
          <span>Loading LDAP servers...</span>
        </div>
      ) : configs.length === 0 ? (
        <Message
          severity="info"
          text="No LDAP servers configured. Add one from Management → LDAP Servers."
          className="w-full justify-content-start"
        />
      ) : (
        configs.map((config) => <LdapServerCard key={config.id} config={config} />)
      )}
    </div>
  );
};
