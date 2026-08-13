/**
 * Edit User Dialog.
 * - Role, Email, Password (shown only when Validate AD is OFF)
 * - All toggles in a single row
 */

import { useEffect, useState } from 'react';
import { useForm, Controller, useWatch } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Dropdown } from 'primereact/dropdown';
import { InputSwitch } from 'primereact/inputswitch';
import { InputText } from 'primereact/inputtext';
import { Password } from 'primereact/password';
import { Button } from 'primereact/button';
import { Dialog } from 'primereact/dialog';
import { useRoles } from '../hooks/useRoles';
import { userApi } from '../api/userApi';
import type { User, UpdateUserRequest } from '../models/User';

const editUserSchema = z.object({
  is_active: z.boolean(),
  is_blocked: z.boolean(),
  is_validate_ad: z.boolean(),
  role_id: z.number().nullable(),
  email: z.string().max(255).nullable(),
  password: z.string().max(128).nullable(),
});

type EditUserFormData = z.infer<typeof editUserSchema>;

interface EditUserDialogProps {
  visible: boolean;
  user: User | null;
  onHide: () => void;
  onSubmit: (userId: number, data: UpdateUserRequest) => void;
  loading?: boolean;
}

export const EditUserDialog = ({ visible, user, onHide, onSubmit, loading }: EditUserDialogProps) => {
  const { roleOptions, loading: rolesLoading } = useRoles();
  const [loadingUserRole, setLoadingUserRole] = useState(false);

  const { handleSubmit, control, register, reset } = useForm<EditUserFormData>({
    resolver: zodResolver(editUserSchema),
    defaultValues: {
      is_active: true,
      is_blocked: false,
      is_validate_ad: true,
      role_id: null,
      email: null,
      password: null,
    },
  });

  // Watch is_validate_ad to conditionally show the password field
  const isValidateAd = useWatch({ control, name: 'is_validate_ad' });

  useEffect(() => {
    if (user && visible) {
      setLoadingUserRole(true);
      userApi.getUserRoles(user.id)
        .then((data) => {
          reset({
            is_active: user.is_active,
            is_blocked: user.is_blocked,
            is_validate_ad: user.is_validate_ad,
            role_id: data.roles.length > 0 ? data.roles[0]!.id : null,
            email: user.email ?? null,
            password: null,
          });
        })
        .catch(() => {
          reset({
            is_active: user.is_active,
            is_blocked: user.is_blocked,
            is_validate_ad: user.is_validate_ad,
            role_id: null,
            email: user.email ?? null,
            password: null,
          });
        })
        .finally(() => setLoadingUserRole(false));
    }
  }, [user, visible, reset]);

  const handleFormSubmit = (data: EditUserFormData) => {
    if (!user) return;
    onSubmit(user.id, {
      is_active: data.is_active,
      is_blocked: data.is_blocked,
      is_validate_ad: data.is_validate_ad,
      role_id: data.role_id,
      email: data.email ?? undefined,
      password: (!data.is_validate_ad && data.password) ? data.password : undefined,
    });
  };

  const footer = (
    <div className="flex justify-content-end gap-2">
      <Button label="Cancel" icon="pi pi-times" severity="secondary" outlined onClick={onHide} />
      <Button label="Save" icon="pi pi-check" loading={loading} onClick={handleSubmit(handleFormSubmit)} />
    </div>
  );

  return (
    <Dialog
      header={`Edit User: ${user?.username || ''}`}
      visible={visible}
      onHide={onHide}
      style={{ width: '480px' }}
      footer={footer}
      modal
      aria-label="Edit user dialog"
    >
      <form className="flex flex-column gap-4 pt-3">
        {/* Username (read-only) */}
        <div className="flex flex-column gap-1">
          <label className="font-medium text-sm">Username</label>
          <span className="text-900 font-semibold">{user?.username}</span>
        </div>

        {/* Email */}
        <div className="flex flex-column gap-2">
          <label htmlFor="edit-email" className="font-medium text-sm">Email Address</label>
          <InputText
            id="edit-email"
            {...register('email')}
            placeholder="e.g. user@example.com"
            type="email"
          />
        </div>

        {/* Role */}
        <div className="flex flex-column gap-2">
          <label htmlFor="edit-role" className="font-medium text-sm">Role</label>
          <Controller
            name="role_id"
            control={control}
            render={({ field }) => (
              <Dropdown
                id="edit-role"
                value={field.value}
                options={roleOptions}
                onChange={(e) => field.onChange(e.value)}
                placeholder={rolesLoading || loadingUserRole ? 'Loading...' : 'Select a role'}
                disabled={rolesLoading || loadingUserRole}
                className="w-full"
                aria-label="Assign role"
              />
            )}
          />
        </div>

        {/* Password — shown only when Validate AD is OFF */}
        {!isValidateAd && (
          <div className="flex flex-column gap-2">
            <label htmlFor="edit-password" className="font-medium text-sm">
              New Password <span className="text-500 font-normal">(leave blank to keep current)</span>
            </label>
            <Controller
              name="password"
              control={control}
              render={({ field }) => (
                <Password
                  id="edit-password"
                  value={field.value ?? ''}
                  onChange={(e) => field.onChange(e.target.value || null)}
                  placeholder="Enter new password"
                  toggleMask
                  feedback={false}
                  inputClassName="w-full"
                  aria-label="New password"
                />
              )}
            />
          </div>
        )}

        {/* All toggles in one row */}
        <div className="flex align-items-center gap-4 flex-wrap">
          <div className="flex align-items-center gap-2">
            <Controller
              name="is_active"
              control={control}
              render={({ field }) => (
                <InputSwitch
                  id="edit-active"
                  checked={field.value}
                  onChange={(e) => field.onChange(e.value)}
                  aria-label="Active"
                />
              )}
            />
            <label htmlFor="edit-active" className="font-medium text-sm cursor-pointer">Active</label>
          </div>

          <div className="flex align-items-center gap-2">
            <Controller
              name="is_blocked"
              control={control}
              render={({ field }) => (
                <InputSwitch
                  id="edit-blocked"
                  checked={field.value}
                  onChange={(e) => field.onChange(e.value)}
                  aria-label="Blocked"
                />
              )}
            />
            <label htmlFor="edit-blocked" className="font-medium text-sm cursor-pointer">Blocked</label>
          </div>

          <div className="flex align-items-center gap-2">
            <Controller
              name="is_validate_ad"
              control={control}
              render={({ field }) => (
                <InputSwitch
                  id="edit-validate-ad"
                  checked={field.value}
                  onChange={(e) => field.onChange(e.value)}
                  aria-label="Validate AD"
                />
              )}
            />
            <label htmlFor="edit-validate-ad" className="font-medium text-sm cursor-pointer">Validate AD</label>
          </div>
        </div>
      </form>
    </Dialog>
  );
};
