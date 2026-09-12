/**
 * Axios client for the PUBLISHED (drop-in) service endpoints.
 *
 * Unlike `apiClient`, these endpoints:
 *  - live at the application root (e.g. /adintegratorservices/rest/v1/*,
 *    /rest/embededsign/v1/*), NOT under /api/v1
 *  - are NOT authenticated with the app JWT; they use an optional shared secret
 *    sent in the `X-API-Key` header (empty = open, drop-in compatible)
 *  - may return XML or bare arrays, so no default JSON content-type is forced
 *
 * This client is used by the "Published Services" test harness so we exercise
 * the exact contract an external consuming application would.
 */

import axios, { type AxiosRequestConfig } from 'axios';

/*
  See apiClient.ts for the rationale: `axios.create` on the default export is the
  documented form, and import/no-named-as-default-member only flags it because axios
  also exports `create` standalone. Silenced per call site, not app-wide.
*/
// eslint-disable-next-line import/no-named-as-default-member
export const publishedApiClient = axios.create({
  baseURL: '/',
  // Published reads (e.g. full employee list / hierarchy) can be large; give
  // them a generous timeout, matching the dev proxy.
  timeout: 120000,
});

/**
 * Build a request config that attaches the `X-API-Key` header only when a
 * (non-empty) key is supplied, preserving open/drop-in behaviour otherwise.
 */
export const withApiKey = (apiKey: string, config: AxiosRequestConfig = {}): AxiosRequestConfig => {
  const key = apiKey.trim();
  if (!key) return config;
  return {
    ...config,
    headers: { ...(config.headers ?? {}), 'X-API-Key': key },
  };
};
