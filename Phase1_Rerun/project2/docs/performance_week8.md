# Week 8 Performance Review

## Query

Latest active transactions for one user, ordered by date.

## ORM relationship loading

The production transaction service uses `selectinload()` for:

- Transaction category
- Transaction payment method

Measured locally with one active transaction:

- Lazy loading: 3 queries
- Eager loading: 3 queries

The dataset is too small to demonstrate query-count growth. The expected
scaling behaviour is that lazy queries grow with distinct relationships,
while eager loading remains approximately three queries.

## Existing indexes reviewed

- `idx_transactions_user_id`
- `idx_transactions_date`
- `idx_transactions_category_id`
- `idx_transactions_user_date`

## PostgreSQL plan

PostgreSQL selected:

- Bitmap Index Scan using `idx_transactions_user_date`
- Bitmap Heap Scan to fetch the matching row
- Filter on `deleted_at IS NULL`
- In-memory quicksort using 25 KB

Measured execution time: 0.646 ms.

## Decision

No new index was added.

The existing `(user_id, date)` index is already used by PostgreSQL. A partial
active-transaction index may be reconsidered when production data volume,
deleted-row volume, or measured latency demonstrates a need.

## Revisit when

- Dashboard latency increases
- The table contains many soft-deleted transactions
- Query plans stop using an appropriate index
- Database CPU, buffers, or connection usage becomes concerning