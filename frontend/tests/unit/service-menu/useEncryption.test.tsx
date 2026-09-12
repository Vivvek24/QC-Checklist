/**
 * Hook test for useEncrypt.
 *
 * Asserts the mutation posts the plaintext to the encrypt endpoint (mocked at
 * the HTTP layer via MSW, so the real apiClient interceptors still run) and
 * surfaces the returned token/encrypted flag.
 */

import type { PropsWithChildren } from 'react';

import { QueryClientProvider } from '@tanstack/react-query';
import { renderHook, waitFor } from '@testing-library/react';
import { http, HttpResponse } from 'msw';
import { describe, expect, it } from 'vitest';

import { useEncrypt } from '@features/service-menu/hooks/useEncryption';

import { server } from '../../mocks/server';
import { createTestQueryClient } from '../../test-utils';

const wrapper = ({ children }: PropsWithChildren) => {
  const queryClient = createTestQueryClient();
  return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>;
};

describe('useEncrypt', () => {
  it('posts the plaintext and returns the token', async () => {
    let capturedBody: { plaintext?: string } | null = null;
    server.use(
      http.post('/api/v1/services/encryption/encrypt', async ({ request }) => {
        capturedBody = (await request.json()) as { plaintext?: string };
        return HttpResponse.json({ token: 'gAAAA-token', encrypted: true });
      }),
    );

    const { result } = renderHook(() => useEncrypt(), { wrapper });

    result.current.mutate('Sep@2026');

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(capturedBody).toEqual({ plaintext: 'Sep@2026' });
    expect(result.current.data).toEqual({ token: 'gAAAA-token', encrypted: true });
  });

  it('surfaces a server error to the caller', async () => {
    server.use(
      http.post('/api/v1/services/encryption/encrypt', () =>
        HttpResponse.json({ detail: 'Permission denied' }, { status: 403 }),
      ),
    );

    const { result } = renderHook(() => useEncrypt(), { wrapper });

    result.current.mutate('anything');

    await waitFor(() => expect(result.current.isError).toBe(true));
  });
});
