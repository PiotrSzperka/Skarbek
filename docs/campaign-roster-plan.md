## Campaign roster (per-parent contributions) — Plan

Goal
----
Allow the skarbnik (admin) to view, for each campaign, the payment record for every parent separately including status, amounts and ability to confirm a payment per parent.

High-level contract
-------------------
- New admin endpoint: GET /api/admin/campaigns/{campaign_id}/roster
  - Purpose: return a list of parents and, for each parent, the related contribution (if any) for the given campaign.
  - Response shape (JSON):

```json
{
  "campaign": { "id": 123, "title": "X", "target_amount": 300.0 },
  "rows": [
    {
      "parent_id": 1,
      "parent_name": "Anna Kowalska",
      "parent_email": "anna@example.com",
      "contribution": {
        "id": 10,
        "amount_expected": 50.0,
        "amount_paid": 50.0,
        "status": "paid",
        "paid_at": "2025-11-03T10:00:00Z",
        "note": "potwierdzone"
      }
    },
    {
      "parent_id": 2,
      "parent_name": "Jan Nowak",
      "parent_email": "jan@example.com",
      "contribution": null
    }
  ]
}
```

Design notes & assumptions
--------------------------
- We will list all parents in the system and LEFT JOIN to contributions for the given campaign. This ensures skarbnik can see who hasn't paid yet.
- Contributions table already has columns: campaign_id, parent_id, amount_expected, amount_paid, status, paid_at, note.
- Admin can use existing endpoint `POST /api/admin/contributions/mark-paid` (or a new endpoint) to mark a contribution as paid for a parent. If no contribution exists for that parent & campaign, admin UI should call a create-contribution endpoint first (we will add `POST /api/admin/contributions` if needed).
- For performance we expect the number of parents per campaign to be moderate (hundreds at most); a single DB query with a LEFT JOIN is fine.
- Backwards-compatibility: code should tolerate older DBs that might lack newly-added columns (defensive try/except already used elsewhere). We will follow the same pattern if necessary.

SQL / Query (conceptual)
------------------------
SELECT p.id as parent_id, p.name, p.email,
       c.id as contribution_id, c.amount_expected, c.amount_paid, c.status, c.paid_at, c.note
FROM parent p
LEFT JOIN contribution c ON c.parent_id = p.id AND c.campaign_id = :campaign_id
WHERE p.is_hidden = false  -- optional filter
ORDER BY p.name

Implementation tasks (files to edit)
-----------------------------------
- Backend
  - `backend/app/api/admin.py` — add new endpoint `GET /admin/campaigns/{id}/roster` and optional `POST /admin/contributions` to create a contribution record.
  - `backend/app/tests/test_admin_roster.py` — new unit/integration test for the endpoint.

- Frontend
  - `frontend/src/api.js` — add `adminCampaignRoster(campaignId, token)` and `adminCreateContribution(payload, token)` helpers.
  - `frontend/src/Admin.jsx` — add a way to open campaign detail / roster (either inline or new component `AdminCampaignDetail.jsx`) and render rows with per-parent status and actions.
  - Optionally update `frontend/tests/...` to include an E2E test that admin can view roster and confirm a payment.

Edge cases
----------
- Parent without contribution -> contribution=null in response (admin can create one).
- Multiple contributions for same (campaign,parent) — we will assume the system uses a single contribution row per parent-per-campaign; if multiples appear take the most recent or the first (implementation will use simple SELECT and expect unique constraint in future).
- Hidden parents: default behaviour is to exclude hidden parents from the roster; admin can pass include_hidden=true to include them if needed.

API security
------------
- Endpoint is admin-only; reuse the existing auth header pattern (Bearer admin_token). The frontend helper will attach the token from localStorage like other admin calls.

Acceptance criteria
-------------------
- GET /api/admin/campaigns/{id}/roster returns campaign info + rows for every (visible) parent with contribution or null.
- Admin UI shows per-parent rows and a button to confirm payment which updates the contribution status to 'paid' and amount_paid/paid_at.
- Backend tests for the roster endpoint pass locally.

Next steps (implementation order)
---------------------------------
1. Implement backend GET roster endpoint and a POST contribution creation endpoint (if missing). Add tests.
2. Add frontend API helpers for roster and create-contribution.
3. Add UI component to view roster and confirm payments.
4. Add E2E smoke test and run locally.
