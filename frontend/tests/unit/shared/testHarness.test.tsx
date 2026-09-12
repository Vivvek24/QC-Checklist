/**
 * Self-test for the shared test harness.
 *
 * Nothing here asserts application behaviour — it asserts that the
 * infrastructure every other test depends on is actually wired up:
 * `renderWithProviders`' provider stack, partial `preloadedState` seeding,
 * the jsdom polyfills from `setup.ts`, and the MSW default handlers.
 *
 * If this file fails, treat every other frontend test failure as suspect
 * until it passes again.
 */

import { describe, expect, it } from 'vitest';

import { server } from '../../mocks/server';
import {
  createTestQueryClient,
  createTestStore,
  renderWithProviders,
  screen,
} from '../../test-utils';

describe('createTestStore', () => {
  it('builds a store with the same slices as the real app store', () => {
    const state = createTestStore().getState();

    expect(state).toHaveProperty('auth');
    expect(state).toHaveProperty('rbac');
  });

  it('accepts a partial preloadedState, seeding one slice and defaulting the rest', () => {
    // This is the whole reason test-utils calls combineReducers() up front:
    // configureStore's own preloadedState would demand every slice here.
    const store = createTestStore({
      rbac: {
        menuKeys: ['employees'],
        menuPermissions: [],
        fieldPermissions: {},
        isLoaded: true,
        isLoading: false,
        error: null,
      },
    });

    const state = store.getState();

    expect(state.rbac.menuKeys).toEqual(['employees']);
    expect(state.rbac.isLoaded).toBe(true);
    // auth was not seeded, so it must still be its reducer's own initial state.
    expect(state.auth).toBeDefined();
  });
});

describe('createTestQueryClient', () => {
  it('disables retries so a failing query fails fast', () => {
    const defaults = createTestQueryClient().getDefaultOptions();

    expect(defaults.queries?.retry).toBe(false);
    expect(defaults.mutations?.retry).toBe(false);
  });
});

describe('renderWithProviders', () => {
  it('mounts a component through the full provider stack', () => {
    renderWithProviders(<div>harness is up</div>);

    expect(screen.getByText('harness is up')).toBeInTheDocument();
  });

  it('returns the store and query client it rendered with', () => {
    const { store, queryClient } = renderWithProviders(<div>x</div>);

    expect(store.getState()).toHaveProperty('rbac');
    expect(queryClient).toBeDefined();
  });
});

describe('jsdom polyfills from setup.ts', () => {
  it('provides the browser APIs PrimeReact mounts against', () => {
    expect(globalThis.ResizeObserver).toBeDefined();
    expect(globalThis.IntersectionObserver).toBeDefined();
    expect(globalThis.matchMedia).toBeDefined();
    expect(Element.prototype.scrollIntoView).toBeDefined();
  });

  it('stubs offsetParent so PrimeReact overlay panels are measurable', () => {
    // jsdom reports null here by default, which leaves opened Dropdown panels
    // stuck at display:none and invisible to every Testing Library query.
    const parent = document.createElement('div');
    const child = document.createElement('div');
    parent.appendChild(child);

    expect(child.offsetParent).toBe(parent);
  });
});

describe('MSW server', () => {
  it('is listening with the default handlers installed', async () => {
    // /auth/refresh is defaulted so that any test rendering a self-loading hook
    // does not fail as an unhandled request.
    const response = await fetch('/api/v1/auth/refresh', { method: 'POST' });

    expect(response.ok).toBe(true);
    await expect(response.json()).resolves.toMatchObject({ token_type: 'Bearer' });
  });

  it('defaults the RBAC menu self-loader to an empty grant', async () => {
    const response = await fetch('/api/v1/rbac/my-permissions/menu');

    await expect(response.json()).resolves.toEqual({ menu_keys: [], permissions: [] });
  });

  it('exposes resetHandlers for per-test overrides', () => {
    expect(typeof server.resetHandlers).toBe('function');
  });
});
