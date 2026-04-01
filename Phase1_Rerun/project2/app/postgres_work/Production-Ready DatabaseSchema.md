Day 2: Production-Ready Database Schema (PostgreSQL)

- Designed and implemented full relational database schema:
  • users table (authentication + identity)
  • categories table (user-specific income/expense categories)
  • transactions table (financial records)

- Added core constraints for data integrity:
  • PRIMARY KEY on all tables
  • FOREIGN KEY relationships:
    - transactions.user_id → users.id (ON DELETE CASCADE)
    - transactions.category_id → categories.id (ON DELETE SET NULL)
    - categories.user_id → users.id (ON DELETE CASCADE)
  • UNIQUE constraints:
    - username, email in users
    - (user_id, name) in categories
  • CHECK constraints:
    - amount > 0 (no invalid transactions)
    - category type IN ('expense', 'income')
    - username minimum length enforced

- Implemented timestamps:
  • created_at and updated_at for audit tracking

- Added performance indexes:
  • idx_transactions_user_id
  • idx_transactions_date
  • idx_transactions_category_id
  • idx_categories_user_id

- Key concepts learned:
  • Difference between CASCADE vs SET NULL
  • Importance of constraints for production safety
  • Why DECIMAL is used instead of FLOAT for financial data
  • Indexing strategy for query optimization

- Outcome:
  Schema is now production-ready, normalized, and optimized for financial data integrity and query performance.