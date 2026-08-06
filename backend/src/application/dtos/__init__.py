"""
Application Data Transfer Objects (DTOs).

DTOs are the contracts between the application layer (services) and the outer
layers (API controllers, scripts). They carry no HTTP concerns — no Pydantic
validators tied to OpenAPI, no `Field` descriptions for docs — just the shape
of the data flowing in and out of each use-case.

API schemas in `api/v1/schemas/` remain the HTTP contract (FastAPI validation,
OpenAPI docs). Controllers map incoming schemas → DTOs → service, and map
outgoing DTOs → response schemas.
"""
