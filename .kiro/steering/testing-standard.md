---
inclusion: always
---

# Testing Standard — Mandatory Coverage

Every new backend service, repository implementation, and domain component ships with a unit
and/or integration test in the same change. Every new frontend hook, form, and page with
logic ships with a Testing Library test in the same change. This is not optional follow-up
work — a PR that adds a class or a component without its test is incomplete, the same way an
endpoint without its service layer would be.

The patterns below were proven in the sibling `enterprise-architecture` repo, which went from
partial coverage to zero test debt in one pass. Copy them, don't reinvent them.

---

## Backend

### Unit tests: services against fake repositories, not a database

**Location:** `backend/tests/unit/application/test_<name>_service.py`

A service's constructor takes repository *interfaces* (per `api-layer-standard.md`), so its
unit test gives it hand-written in-memory fakes, not a mock library and not a real database.
`unittest.mock.AsyncMock` is not the convention here — a repository fake is a small
hand-written class implementing the same `I<Entity>Repository` interface with a `dict` for
storage, grouped into a `*_fakes.py` module next to the tests that use it
(`darwinbox_fakes.py`, `rbac_fakes.py`, ...).

```python
# tests/unit/application/darwinbox_fakes.py
class FakeDarwinboxEmployeeRepository(IDarwinboxEmployeeRepository):
    def __init__(self) -> None:
        self.rows: dict[str, DarwinboxEmployee] = {}

    async def get_by_employee_id(self, employee_id: str) -> DarwinboxEmployee | None:
        # Deep copy: a caller mutating the result must not leak back into storage.
        return copy.deepcopy(self.rows.get(employee_id))

    async def create(self, employee: DarwinboxEmployee) -> DarwinboxEmployee:
        self.rows[employee.employee_id] = copy.deepcopy(employee)
        return copy.deepcopy(employee)

    async def bulk_upsert(self, employees: list[DarwinboxEmployee]) -> None:
        for e in employees:
            self.rows[e.employee_id] = copy.deepcopy(e)
```

```python
# tests/unit/application/test_darwinbox_service.py
@pytest.fixture
def repo() -> FakeDarwinboxEmployeeRepository:
    return FakeDarwinboxEmployeeRepository()

@pytest.fixture
def service(repo: FakeDarwinboxEmployeeRepository) -> DarwinboxService:
    return DarwinboxService(client=FakeDarwinboxClient(), repository=repo)

class TestSync:
    async def test_payload_without_employee_id_is_counted_as_failed(
        self, service: DarwinboxService, actor: User
    ) -> None:
        result = await service.sync_employees(actor, ["active"])

        assert result.failed == 1
```

**What a new service's unit tests must cover:**
- Every business rule the service enforces beyond basic CRUD — existence checks, uniqueness
  (and its scope: global vs. per-parent), status/state validation, delete guards.
- Every branch of a partial `update_*` method, one test per field that changes independently.
  When a service re-validates a downstream field after an upstream one changes, write the
  test for the *unusual order* explicitly — that is exactly the class of bug a single such
  test catches and no end-to-end test does.
- Every mapping function that names an external payload key. A field added to a sync mapper
  needs a test for present / missing / `None` / whitespace-padded, because all four are real
  shapes an upstream API sends (see `test_darwinbox_employee_mapping.py`).
- Class-grouped `Test<Action>` names (`TestCreate`, `TestUpdate`, `TestDelete`), no shared
  mutable state between tests — each test builds its own fresh fake repo via the `repo`
  fixture.

Domain/application services with no persistence follow the same shape: fakes for their
dependencies, one test per transition/branch, not one giant end-to-end test.

### Integration tests: repository implementations against a real database

**Location:** `backend/tests/integration/database/test_<entity>_repository_impl.py`

Repository implementations are SQL, and SQL filter/join/uniqueness behavior cannot be
meaningfully faked — these use the real `db_session` fixture (a Postgres transaction rolled
back after each test), not an in-memory substitute.

```python
class TestBulkUpsert:
    async def test_existing_employee_id_updates_instead_of_duplicating(
        self, db_session: AsyncSession
    ) -> None:
        repo = DarwinboxEmployeeRepositoryImpl(db_session)
        await repo.create(_employee("E1", department="Old"))

        await repo.bulk_upsert([_employee("E1", department="New")])

        assert (await repo.get_by_employee_id("E1")).department == "New"
        assert await repo.count() == 1
```

**What a new repository impl's tests must cover:**
- `create`/`get_by_id`/`update`/`delete`, and every `exists_by_*` (including the scoping —
  global vs. parent-scoped — and any `exclude_id` behavior used during updates).
- `list_all` with each supported filter combination (search, status, every parent-id filter)
  plus pagination and ordering; `count` mirroring the same filters.
- The on-conflict branch of any `bulk_upsert`, not just the insert branch.
- `has_dependents` against each entity type that actually references this one via FK.
- Entity ↔ ORM model mapping round-trips correctly for every field, including nullable
  columns (a `NULL` column must round-trip as `None`, not `''`).

Anything that isn't behind a repository port and instead does raw ORM work directly against
`AsyncSession` (`permission_manager.py` is the existing example, taking `AsyncSession`
because it has no interface to fake) is still an integration test in
`tests/integration/database/`, not a unit test — the same reasoning as above applies: no
interface exists to fake, so the real database is the only option that tests anything real.

### External HTTP clients: mock the transport, not the client

**Location:** `backend/tests/unit/infrastructure/test_<name>_client.py`

`darwinbox_client.py`, `employee_ad_client.py`, `esigner_client.py`, and `azure_client.py`
all wrap `httpx`. Test them with `httpx.MockTransport`, so the real request construction
(auth headers, body shape, URL) is exercised and asserted. Do not monkeypatch the client's
own methods — that tests nothing.

### Directory convention — do not mirror `src/`

Tests are flat files grouped **one level deep by layer**, matching what already exists:
`tests/unit/domain/`, `tests/unit/application/`, `tests/unit/infrastructure/`,
`tests/integration/`, `tests/integration/database/`, `tests/integration/api/`. A new service
test is a sibling file in `tests/unit/application/`, not a new subdirectory mirroring
`src/application/services/`.

### Checklist — new backend service/repository/endpoint

- [ ] Service has a fake repository in the relevant `*_fakes.py` (or a new one, matching the
      existing hand-written, deep-copy, `dict`-backed pattern)
- [ ] Service has `tests/unit/application/test_<name>_service.py` covering every business
      rule, every independent branch of partial updates, and the delete guard
- [ ] Repository implementation has `tests/integration/database/test_<entity>_repository_impl.py`
      covering CRUD, uniqueness scoping, filters/pagination, the bulk-upsert conflict branch,
      and entity↔model round-trips for nullable fields
- [ ] New API endpoints touching auth/session state get an integration test in
      `tests/integration/test_auth_api.py` or `tests/integration/api/` using
      `app.dependency_overrides`, not `unittest.mock.patch` (patching a module attribute
      after FastAPI has already resolved `Depends(...)` at route-declaration time has no
      effect on the registered route)
- [ ] Published-contract endpoints (`/adintegratorservices/rest/v1/*`,
      `/esignerservices/*`) get a test asserting the wire format by alias —
      `model_dump(by_alias=True)` must still emit `territory_code_(sales_hq_code)` and the
      PascalCase Mendix keys. These are drop-in replacements for a legacy service; a renamed
      key is a breaking change for every consumer.
- [ ] `pytest -q` (full suite), `ruff check src scripts tests`, `mypy src tests scripts`,
      `alembic check` all pass before considering the change done

---

## Frontend

### Test infrastructure — reuse it, do not recreate it

`jsdom`, `@testing-library/jest-dom`, `@testing-library/user-event`, `msw`, and
`@vitest/coverage-v8` are installed and pinned exact in `frontend/package.json`. Reuse:

- `frontend/tests/setup.ts` — jest-dom matchers, RTL auto-cleanup, PrimeReact polyfills
- `frontend/tests/test-utils.tsx` — `renderWithProviders`, `createTestStore`,
  `createTestQueryClient`, plus the PrimeReact dropdown helpers below
- `frontend/tests/mocks/server.ts` — the shared MSW server and its default handlers for
  self-loading RBAC endpoints

Do not install a different testing library, do not write a second render helper, and do not
hand-roll a `QueryClientProvider`/`Provider` wrapper inline in a test file.

### Where tests live

**Location:** `frontend/tests/unit/<area>/<Name>.test.tsx` — areas mirror `src/features/`
and `src/shared/`: `auth/`, `rbac/`, `shared/`, `employee-directory/`, `service-menu/`,
`user-management/`. Tests are **not** colocated with `src/` — `tsconfig.test.json` and
`vite.config.ts`'s `test.include` both expect `tests/**/*.{test,spec}.{ts,tsx}`.

### `renderWithProviders`

Mirrors the real provider stack from `App.tsx` (Redux `Provider` → `QueryClientProvider` →
`PrimeReactProvider` → `MemoryRouter`). Use it for anything that renders a component; use the
bare `createTestStore`/`createTestQueryClient` plus `renderHook` for hook-only tests.

```tsx
renderWithProviders(<EmployeeDirectoryPage />, {
  preloadedState: {
    rbac: { ...defaultRbacState, menuKeys: ['employees'], isLoaded: true },
  },
});
```

Note this service's `rbacSlice` exposes `menuKeys` / `menuPermissions` /
`fieldPermissions` / `isLoaded` — there is no `my-permissions/api` endpoint here and
correspondingly no `apiResourceActions` / `isApiLoaded`. API-level authorisation is
enforced server-side by `require_permission()`; the frontend gates on menu and field
scopes only.

`preloadedState` is typed `TestPreloadedState` (exported from `test-utils.tsx`) — **not**
`PreloadedState<RootState>` imported from `@reduxjs/toolkit`, which Redux Toolkit 2.x no
longer exports.

### Mocking the network: MSW, not `vi.mock('axios')`

Every API-touching test uses `server.use(http.get(...), ...)` from `tests/mocks/server.ts`,
mocking at the HTTP layer so the real `apiClient` interceptors (token attach, 401 refresh
retry) still run. Default handlers for `/auth/refresh` and the RBAC `my-permissions/*`
endpoints already exist precisely so that a test focused on something else doesn't have to
stub them — override with `server.use()` only when the test actually cares about that
endpoint's response.

### Testing PrimeReact Dropdown/Dialog — read this before writing a new one

Three non-obvious fixes make PrimeReact overlays testable under jsdom at all; they live in
`tests/setup.ts` and `tests/test-utils.tsx` already and must not be reverted:

1. **`cssTransition: false`** is passed to `PrimeReactProvider` in `test-utils.tsx`. Without
   it, `react-transition-group`'s enter/leave animation never completes under jsdom (no real
   animation-frame timing), and an opened panel stays invisible to every query.
2. **`HTMLElement.prototype.offsetParent`** is stubbed in `tests/setup.ts` to return
   `parentNode`. jsdom has no layout engine and always reports `offsetParent` as `null`,
   which sends PrimeReact's `DomHandler.absolutePosition()` down the branch that measures a
   panel by briefly flipping it to `display: block` and back to `display: none` — leaving it
   hidden. This is the fix for a Dropdown/MultiSelect/Calendar panel silently staying
   `display: none` after a click that "worked."
3. **Never click a Dropdown's accessible `<input>` directly.** `getByLabelText('Status')`
   finds PrimeReact's hidden a11y input, which has `pointer-events: none` — the click
   throws. Use the helpers exported from `test-utils.tsx` instead:

```tsx
// Opens the dropdown via its real trigger element, then clicks the option by accessible name.
await selectDropdownOption(user, 'Status', 'Active');

// Reads the *closed* dropdown's displayed label — not screen.getByText(label), which also
// matches PrimeReact's hidden native <select><option> fallback and throws on ambiguity.
expect(getDropdownLabel('Status')).toBe('Active');

// Scopes to the zod error specifically — a required Dropdown's own placeholder often reads
// identically to its validation message.
expect(getValidationError('Select a status')).toBeInTheDocument();
```

An empty-string sentinel option renders as a *blank* closed label regardless of which option
maps to it — do not assert the closed label for that case; assert the option exists in the
open panel, and that the sentinel round-trips through submit (as `null`) instead.

### Fixture IDs must satisfy the schema's own validation

Where a zod schema validates an id with `z.string().uuid()`, a fixture id like `'user-1'` is
not a UUID — the form fails silent client-side validation and `onSubmit` never fires, which
reads exactly like a broken test until you notice the `p-invalid` class still on the field.
Use real UUID-shaped strings (`'11111111-1111-1111-1111-111111111111'`) for any id fixture.

### Checklist — new hook/component/page

- [ ] Any component with conditional rendering, a permission gate, or an async data
      dependency gets its own `tests/unit/<area>/<Name>.test.tsx`
- [ ] A data hook gets a test covering: the filter params actually reach the request, and a
      create/update/delete invalidates exactly its declared dependent query keys (no more,
      no fewer)
- [ ] A form gets a test covering every zod validation rule, create-vs-edit header and field
      reset, submit-time normalisation (trim/case, empty-string→`null`), and any cascading
      dropdown (`useWatch` + a child lookup keyed on the parent's current value)
- [ ] A page gets render, permission-gated action buttons, and at least one end-to-end
      interaction (create or delete) including the conflict/error path
- [ ] A Redux slice's thunks get one test per outcome (fulfilled + rejected) against a real
      reducer via `configureStore`, mocking only the network (MSW), not the thunk itself
- [ ] A slice whose `initialState` hydrates from `sessionCache` at module-import time needs a
      `<Slice>.hydration.test.ts` using `vi.resetModules()` + dynamic `import()` to exercise
      both the cold-start and cache-warm shapes — a static top-level import only ever sees one
- [ ] `npm run build`, `npm run type-check`, `npm run lint`, `npm test` all pass before
      considering the change done

### Version discipline

`vitest`/`@vitest/coverage-v8` must stay on a version whose own `vite` dependency range
includes the project's actual `vite` version (check `npm view vitest@<version> dependencies`
before bumping either). A mismatch does not fail loudly — npm silently installs a second,
nested `vite` copy for vitest's resolution, and `vite.config.ts`'s `test` block then fails
type-checking with `'test' does not exist in type 'UserConfigExport'` because the two
`vite` packages have structurally incompatible `Plugin`/`UserConfig` types.
