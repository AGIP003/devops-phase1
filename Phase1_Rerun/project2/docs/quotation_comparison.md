# Quotation comparison

The quotation workspace helps an authenticated user compare supplier offers against one shared list of requested items. It is a decision-support feature: the software shows evidence, while the user chooses the preferred supplier.

## Business rules

- Every comparison belongs to one user. All reads and mutations include the authenticated user's ID, so guessing another project's integer ID returns `404`.
- A supplier offer is complete only when it includes a price for every requested item.
- Only complete offers can receive the **Lowest cost** label. Missing prices must never make an incomplete offer appear cheaper.
- **Lowest cost** is calculated; **Preferred supplier** is selected by the user. They may be different.
- PostgreSQL enforces at most one preferred supplier per project with a partial unique index.
- Deleting a project cascades to its items, quotations and prices. Deleting an item removes that item's supplier prices.
- API money values are decimal strings. The server performs currency arithmetic with Python `Decimal`; the frontend does not replace the server's landed-total calculation.

The landed total is:

```text
item subtotal + delivery cost + excluded tax - discount
```

The result cannot be lower than zero. Tax is added only when `taxMode` is `excluded`; `included` means it is already present in supplier item prices.

## Data model

```text
users
  └── quotation_projects
        ├── quotation_items
        └── supplier_quotations
              └── supplier_quotation_prices ──> quotation_items
```

`supplier_quotation_prices` is a junction table: one quotation has many item prices, and each price identifies the shared requested item it covers.

## API

All endpoints require the existing bearer-token authentication middleware.

- `GET|POST /api/quotation-projects`
- `GET|PATCH|DELETE /api/quotation-projects/<project_id>`
- `POST /api/quotation-projects/<project_id>/items`
- `PATCH|DELETE /api/quotation-projects/<project_id>/items/<item_id>`
- `POST /api/quotation-projects/<project_id>/quotes`
- `PATCH|DELETE /api/quotation-projects/<project_id>/quotes/<quote_id>`
- `PATCH /api/quotation-projects/<project_id>/quotes/<quote_id>/preference`

Private responses use `Cache-Control: private, no-store` because supplier contacts and purchasing decisions are user data.

## Verification and deployment

The integration tests cover landed-cost calculation, incomplete offers, object-level ownership and preferred-supplier uniqueness. The migration was downgrade/upgrade tested on `finance_tracker_test` before production use.

Deploy the application code and run `flask db upgrade` through the existing Railway pre-deploy command. Do not run `db.create_all()` or destructive test cleanup against Railway.

PDF generation is deliberately outside this change. Quotation PDFs and transaction-report PDFs will share a separately designed document-generation lesson, including authorization, data selection, rendering, download headers and tests.
