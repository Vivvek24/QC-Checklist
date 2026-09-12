# Darwinbox Employee Sync Service

## Overview

The Darwinbox Service integrates the Emcure Darwinbox **master employee API** as an external service within the enterprise architecture. Unlike the read-only Employee AD proxy, this service **persists** the full employee master (active + inactive) into a local `darwinbox_employees` table so the application owns a queryable copy of the workforce data.

It follows the project's Clean/DDD layering: thin controller → application service → repository (Port) → repository implementation (Adapter), with a domain entity, DTO schemas, and an external client adapter.

**Darwinbox Master API URL:**
```
https://emcure.darwinbox.in/masterapi/employee
```

The endpoint uses HTTP Basic auth plus a JSON body carrying `api_key` and `datasetKey`, and returns `{ status, message, employee_data: [...] }`.

---

## Architecture

```
┌───────────────────────────────────────────────────────────────────────┐
│  Backend (FastAPI)                                                      │
│                                                                         │
│  ┌───────────────────────────────────────────────────────────────────┐ │
│  │ API Layer (thin): darwinbox_controller.py                         │ │
│  │ Router prefix: /api/v1/services/darwinbox                         │ │
│  │ Dependencies: [require_permission("services.darwinbox")]          │ │
│  │  GET  /health   GET /employees   GET /stored   POST /sync         │ │
│  └───────────────────────────────────┬───────────────────────────────┘ │
│                                       │ delegates to                    │
│  ┌───────────────────────────────────▼───────────────────────────────┐ │
│  │ Application Layer: DarwinboxService                               │ │
│  │  - check_health / fetch_remote_employees / sync_employees / list  │ │
│  │  - maps Darwinbox payload → DarwinboxEmployee entity              │ │
│  └──────────────┬──────────────────────────────────┬─────────────────┘ │
│                 │ external adapter                  │ persistence port  │
│  ┌──────────────▼───────────────┐   ┌───────────────▼─────────────────┐ │
│  │ Infrastructure/external:     │   │ Domain Port:                    │ │
│  │ DarwinboxClient (httpx)      │   │ IDarwinboxEmployeeRepository    │ │
│  │  - Basic auth + JSON body    │   │        ▲ implemented by         │ │
│  │  - exception hierarchy       │   │ DarwinboxEmployeeRepositoryImpl │ │
│  └──────────────┬───────────────┘   │  (SQLAlchemy async, _to_entity) │ │
│                 │ HTTPS               └───────────────┬─────────────────┘ │
└─────────────────┼───────────────────────────────────┼───────────────────┘
                  │                                    │
   ┌──────────────▼─────────────┐        ┌─────────────▼──────────────┐
   │ Darwinbox Master API       │        │ PostgreSQL                 │
   │ POST /masterapi/employee   │        │ table: darwinbox_employees │
   └────────────────────────────┘        └────────────────────────────┘
```

---

## File Structure

```
backend/src/
├── api/v1/
│   ├── endpoints/
│   │   └── darwinbox_controller.py                 # Thin REST controller (4 endpoints)
│   ├── schemas/
│   │   └── darwinbox_schema.py                     # Request/response DTOs
│   ├── dependencies.py                             # get_darwinbox_employee_repository
│   └── router.py                                   # Registers darwinbox_router
├── application/services/
│   └── darwinbox_service.py                        # Application service (orchestration)
├── config/
│   ├── settings.py                                 # DARWINBOX_* settings
│   └── dependency_injection.py                     # Container wiring
├── domain/
│   ├── entities/darwinbox_employee.py              # Domain entity
│   └── repositories/darwinbox_employee_repository.py  # Repository interface (Port)
└── infrastructure/
    ├── database/
    │   ├── models/darwinbox_employee_model.py      # SQLAlchemy ORM model
    │   ├── repositories/darwinbox_employee_repository_impl.py  # Adapter
    │   └── migrations/versions/f3a4b5c6d7e8_create_darwinbox_employees_table.py
    └── external/darwinbox/
        ├── __init__.py
        └── darwinbox_client.py                     # httpx async client
```

---

## Configuration

Active and inactive employees come from the **same URL** but use different Basic-auth credentials and `api_key`/`datasetKey` values. These are modelled as two datasets: **active** and **inactive**.

| Environment Variable | Description |
|---------------------|-------------|
| `DARWINBOX_BASE_URL` | Darwinbox master employee API URL (shared by both datasets) |
| `DARWINBOX_USERNAME` / `DARWINBOX_PASSWORD` | Basic auth for the **active** dataset |
| `DARWINBOX_API_KEY` / `DARWINBOX_DATASET_KEY` | `api_key` / `datasetKey` for the **active** dataset |
| `DARWINBOX_INACTIVE_USERNAME` / `DARWINBOX_INACTIVE_PASSWORD` | Basic auth for the **inactive** dataset |
| `DARWINBOX_INACTIVE_API_KEY` / `DARWINBOX_INACTIVE_DATASET_KEY` | `api_key` / `datasetKey` for the **inactive** dataset |

`is_configured(dataset)` returns true only when the base URL and that dataset's four values are all set.

---

## API Endpoints

All endpoints require JWT authentication and the **`services.darwinbox`** permission.

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/services/darwinbox/health` | Check reachability + per-dataset configured flags |
| GET | `/api/v1/services/darwinbox/employees?dataset=active\|inactive` | Fetch the raw employee master for a dataset (no persistence) |
| GET | `/api/v1/services/darwinbox/stored` | List employees already synced into the DB (paginated, optional `status` filter) |
| POST | `/api/v1/services/darwinbox/sync?scope=active\|inactive\|all` | Fetch the selected dataset(s) and upsert into the DB (default `all`) |

### Health Check
```json
{
  "service": "Darwinbox (Employee Master)",
  "active_configured": true,
  "inactive_configured": true,
  "base_url": "https://emcure.darwinbox.in/masterapi/employee",
  "status": "reachable",
  "status_code": 200,
  "url": "https://emcure.darwinbox.in/masterapi/employee"
}
```

### Sync (both populations)
```http
POST /api/v1/services/darwinbox/sync?scope=all
Authorization: Bearer <jwt-token>
```
```json
{
  "datasets": ["active", "inactive"],
  "total": 1500,
  "created": 1450,
  "updated": 50,
  "failed": 0,
  "message": "active: Successfully loaded all employees data | inactive: Successfully loaded all employees data"
}
```

### List Stored (active only)
```http
GET /api/v1/services/darwinbox/stored?status=Active&skip=0&limit=100
Authorization: Bearer <jwt-token>
```

---

## Sync Behaviour

- Records are keyed on `employee_id` (unique, indexed).
- New employee → **created**; existing employee → **updated** in place (audit `created_*` preserved, `modified_*` refreshed).
- Rows without an `employee_id` or that error during upsert are counted as **failed** and skipped; the sync continues.
- `employee_status` and `company_email_id` are indexed to support active/inactive and email lookups.

---

## Error Handling

The client maps Darwinbox HTTP errors to service exceptions; the controller maps those to HTTP responses.

| Darwinbox Status | Our Response | Exception |
|------------------|--------------|-----------|
| 401, 403 | 401 Unauthorized | `DarwinboxAuthError` |
| Other HTTP errors / bad payload | 502 Bad Gateway | `DarwinboxError` |
| Connection failure | 503 Service Unavailable | `DarwinboxUnavailableError` |

---

## Security

| Layer | Mechanism |
|-------|-----------|
| Backend Router | `dependencies=[Depends(require_permission("services.darwinbox"))]` |
| RBAC seed | `services.darwinbox` permission granted to ADMIN (see `scripts/seed_rbac.py`) |
| Transport to Darwinbox | HTTPS, HTTP Basic auth, secret `api_key`/`datasetKey` sourced from env |

> **Note:** The stored master contains PII (PAN, date of birth, personal mobile). Access is gated by RBAC. Consider field-level permissions (as used for salary/email/phone) if narrower visibility is required.

---

## Database Migration

```bash
alembic upgrade head    # creates the darwinbox_employees table (revision f3a4b5c6d7e8)
python scripts/seed_rbac.py   # registers the services.darwinbox permission
```
