/**
 * Country master API calls.
 * Maps to backend: /api/v1/masters/countries
 */

import { createMasterApi } from './createMasterApi';
import type {
  Country,
  CountryListParams,
  CreateCountryRequest,
  UpdateCountryRequest,
} from '../models/Country';

export const countryApi = createMasterApi<
  Country,
  CreateCountryRequest,
  UpdateCountryRequest,
  CountryListParams
>('/masters/countries', 'countries');
