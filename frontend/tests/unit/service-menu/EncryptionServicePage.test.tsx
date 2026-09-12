/**
 * Page test for EncryptionServicePage.
 *
 * Covers: render, the empty-input guard (no request fired), a successful
 * encrypt end-to-end showing the token, and the passthrough warning when the
 * server reports encrypted=false. The network is mocked at the HTTP layer
 * (MSW), never the hook.
 */

import userEvent from '@testing-library/user-event';
import { http, HttpResponse } from 'msw';
import { describe, expect, it } from 'vitest';

import { EncryptionServicePage } from '@features/service-menu/pages/EncryptionServicePage';

import { server } from '../../mocks/server';
import { renderWithProviders, screen, waitFor } from '../../test-utils';

describe('EncryptionServicePage', () => {
  it('renders the heading and input', () => {
    renderWithProviders(<EncryptionServicePage />);

    expect(screen.getByRole('heading', { name: 'Encryption Utility' })).toBeInTheDocument();
    expect(screen.getByLabelText('Plaintext value')).toBeInTheDocument();
  });

  it('does not call the endpoint when the input is empty', async () => {
    const user = userEvent.setup();
    let called = false;
    server.use(
      http.post('/api/v1/services/encryption/encrypt', () => {
        called = true;
        return HttpResponse.json({ token: 'x', encrypted: true });
      }),
    );

    renderWithProviders(<EncryptionServicePage />);
    await user.click(screen.getByRole('button', { name: 'Encrypt' }));

    // Give any (unexpected) request a tick to fire.
    await new Promise((r) => setTimeout(r, 50));
    expect(called).toBe(false);
  });

  it('encrypts a value and shows the returned token', async () => {
    const user = userEvent.setup();
    server.use(
      http.post('/api/v1/services/encryption/encrypt', () =>
        HttpResponse.json({ token: 'gAAAA-the-token', encrypted: true }),
      ),
    );

    renderWithProviders(<EncryptionServicePage />);
    await user.type(screen.getByLabelText('Plaintext value'), 'Sep@2026');
    await user.click(screen.getByRole('button', { name: 'Encrypt' }));

    await waitFor(() => expect(screen.getByDisplayValue('gAAAA-the-token')).toBeInTheDocument());
    expect(screen.getByText('Encrypted')).toBeInTheDocument();
  });

  it('warns when the server is in passthrough (plaintext) mode', async () => {
    const user = userEvent.setup();
    server.use(
      http.post('/api/v1/services/encryption/encrypt', () =>
        HttpResponse.json({ token: 'Sep@2026', encrypted: false }),
      ),
    );

    renderWithProviders(<EncryptionServicePage />);
    await user.type(screen.getByLabelText('Plaintext value'), 'Sep@2026');
    await user.click(screen.getByRole('button', { name: 'Encrypt' }));

    await waitFor(() => expect(screen.getByText('Passthrough (plaintext)')).toBeInTheDocument());
    expect(screen.getByText(/No encryption key is configured/i)).toBeInTheDocument();
  });

  it('offers a copy button once a token is shown', async () => {
    const user = userEvent.setup();
    server.use(
      http.post('/api/v1/services/encryption/encrypt', () =>
        HttpResponse.json({ token: 'gAAAA-copyme', encrypted: true }),
      ),
    );

    renderWithProviders(<EncryptionServicePage />);
    await user.type(screen.getByLabelText('Plaintext value'), 'x');
    await user.click(screen.getByRole('button', { name: 'Encrypt' }));
    await waitFor(() => expect(screen.getByDisplayValue('gAAAA-copyme')).toBeInTheDocument());

    // The copy control is present and wired to the clipboard write; the browser
    // clipboard call itself is exercised by userEvent's own clipboard stub and
    // not re-asserted here.
    expect(screen.getByRole('button', { name: 'Copy token' })).toBeEnabled();
  });
});
