/**
 * RBAC Redux slice.
 * Manages the user's permissions state fetched from the backend.
 * Loaded after authentication and used throughout the app.
 */

import type { PayloadAction } from '@reduxjs/toolkit';
import { createAsyncThunk, createSlice } from '@reduxjs/toolkit';

import { sessionCache } from '@shared/services/sessionCache';
import { extractApiError } from '@shared/utils/apiError';

import { rbacApi } from './rbacApi';
import type {
  FieldPermissionsResponse,
  MenuPermissionsResponse,
  Permission,
  PermissionAction,
} from './types';

interface RbacState {
  /** Menu keys the user can access */
  menuKeys: string[];
  /** All menu permissions for detailed checks */
  menuPermissions: Permission[];
  /** Field-level permissions by resource */
  fieldPermissions: Record<string, Record<string, PermissionAction[]>>;
  /** Whether RBAC data has been loaded */
  isLoaded: boolean;
  isLoading: boolean;
  error: string | null;
}

// Hydrate from the cached snapshot so navigation guards resolve immediately on a
// remount instead of blanking while menu permissions are refetched.
const cachedMenuKeys = sessionCache.getMenuKeys();
const cachedPermissions = sessionCache.getPermissions();

const initialState: RbacState = {
  menuKeys: cachedMenuKeys,
  menuPermissions: cachedPermissions,
  fieldPermissions: {},
  isLoaded: cachedMenuKeys.length > 0,
  isLoading: false,
  error: null,
};

/**
 * Fetch menu permissions after login.
 */
export const fetchMenuPermissions = createAsyncThunk(
  'rbac/fetchMenuPermissions',
  async (_, { rejectWithValue }) => {
    try {
      return await rbacApi.getMenuPermissions();
    } catch (error) {
      return rejectWithValue(extractApiError(error, 'Failed to load permissions'));
    }
  },
);

/**
 * Fetch field-level permissions for a specific resource (lazy-loaded).
 */
export const fetchFieldPermissions = createAsyncThunk(
  'rbac/fetchFieldPermissions',
  async (resource: string, { rejectWithValue }) => {
    try {
      return await rbacApi.getFieldPermissions(resource);
    } catch (error) {
      return rejectWithValue(extractApiError(error, 'Failed to load field permissions'));
    }
  },
);

const rbacSlice = createSlice({
  name: 'rbac',
  initialState,
  reducers: {
    clearRbac: () => {
      sessionCache.clear();
      return { ...initialState, menuKeys: [], menuPermissions: [], isLoaded: false };
    },
  },
  extraReducers: (builder) => {
    builder
      // Menu permissions
      .addCase(fetchMenuPermissions.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(
        fetchMenuPermissions.fulfilled,
        (state, action: PayloadAction<MenuPermissionsResponse>) => {
          state.isLoading = false;
          state.isLoaded = true;
          state.menuKeys = action.payload.menu_keys;
          state.menuPermissions = action.payload.permissions;
          sessionCache.setRbac(action.payload.menu_keys, action.payload.permissions);
        },
      )
      .addCase(fetchMenuPermissions.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload as string;
      })
      // Field permissions
      .addCase(
        fetchFieldPermissions.fulfilled,
        (state, action: PayloadAction<FieldPermissionsResponse>) => {
          state.fieldPermissions[action.payload.resource] = action.payload.fields;
        },
      );
  },
});

export const { clearRbac } = rbacSlice.actions;
export default rbacSlice.reducer;
