import { createMasterApi } from './createMasterApi';
import type { Format, FormatListParams, CreateFormatRequest, UpdateFormatRequest } from '../models/Format';

export const formatApi = createMasterApi<Format, CreateFormatRequest, UpdateFormatRequest, FormatListParams>(
  '/masters/formats', 'items'
);
