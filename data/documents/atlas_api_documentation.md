---
id: doc_api_docs_atlas
title: Atlas Reports API Documentation
type: API Documentation
author_id: arun_kumar
created_at: 2026-08-25
updated_at: 2026-10-05
project_id: atlas
team_id: team_backend
source_path: data/documents/atlas_api_documentation.md
---

# Atlas Reports API

Base URL: `https://atlas.novatech.example/api/v2`

All endpoints require a bearer token issued by the Auth Gateway and an `X-Purpose` header
describing the business purpose of the request (required for PII audit logging per ATLAS-110).

## GET /reports/usage

Returns usage aggregates for the caller's tenant.

**Query parameters**

| Name | Type | Description |
| --- | --- | --- |
| `from` | date | Inclusive period start |
| `to` | date | Inclusive period end |
| `plan` | string | Optional plan filter |
| `region` | string | Optional region filter |
| `group_by` | string | `day`, `week` or `month` |

**Response**

```json
{
  "tenant_id": "t_8421",
  "period": {"from": "2026-09-01", "to": "2026-09-30"},
  "reports": [
    {"bucket": "2026-09-01", "sum": 18402, "unit": "api_calls", "plan": "scale"}
  ],
  "staleness_seconds": 42
}
```

The response is served from the read replica; `staleness_seconds` tells the client how far behind
the replica is so the UI can show a freshness badge.

## GET /customers/{id}

Returns the customer record with plan and region. Sensitive fields are redacted unless the caller
carries the `customer:pii` scope.

## Error codes

| Code | Meaning |
| --- | --- |
| 401 | Missing or invalid token |
| 403 | Missing scope |
| 409 | Schema version mismatch (see ATLAS-107) |
| 429 | Rate limited, retry after `Retry-After` |
| 503 | Replica unavailable, retry with backoff |

## Notes for consumers

Mercury consumes `/reports/usage` and must tolerate `staleness_seconds` up to 120 before alerting.
The `sum` field name is stable since v2.8 (contract drift fixed under MERCURY-304).
