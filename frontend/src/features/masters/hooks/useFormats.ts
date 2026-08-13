import { formatApi } from '../api/formatApi';
import { createMasterHooks } from './createMasterHooks';
import { MASTER_KEYS } from './masterQueryKeys';
import type { Format, FormatListParams, CreateFormatRequest, UpdateFormatRequest } from '../models/Format';

const hooks = createMasterHooks<Format, CreateFormatRequest, UpdateFormatRequest, FormatListParams>(
  formatApi, MASTER_KEYS.formats
);

export const useFormats = hooks.useList;
export const useCreateFormat = hooks.useCreate;
export const useUpdateFormat = hooks.useUpdate;
export const useDeleteFormat = hooks.useDelete;
