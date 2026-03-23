Concepts to learn: Core Concepts — SELECT & WHERE
• SELECT: Retrieving specific columns vs SELECT * (always specify columns in production)
• WHERE: Filtering rows with conditions (=, >, <, >=, <=, !=, IN, LIKE, BETWEEN)
• AND/OR/NOT: Combining multiple conditions (use parentheses to control precedence)
• ORDER BY: Sorting results ASC (default) or DESC, can sort by multiple columns
• LIMIT: Restricting number of rows (PostgreSQL) vs TOP (SQL Server)
• DISTINCT: Removing duplicates (expensive operation, use wisely)
• NULL handling: IS NULL vs IS NOT NULL (never use = NULL, it returns nothing)
• String operations: LIKE '%pattern%' for partial matches, ILIKE for case-insensitive (PostgreSQL)

    Concepts to learn:JOINs
    • INNER JOIN: Returns ONLY rows where match exists in BOTH tables
      - Example: Users with transactions (excludes users who never transacted)
      - Most common join type in practice
    • LEFT JOIN (LEFT OUTER JOIN): Returns ALL rows from left table + matching rows from right (NULLs where no match)
      - Example: All users even if they have zero transactions
      - Critical for "show everyone" queries
    • RIGHT JOIN: Opposite of LEFT (rare in practice — just flip your LEFT JOIN)
    • FULL OUTER JOIN: All rows from both tables (rarely needed)
    • JOIN vs ON vs WHERE: ON filters during join, WHERE filters after join (affects LEFT JOIN results)
    • JOIN order matters: FROM users LEFT JOIN transactions is different than FROM transactions LEFT JOIN users
    • Table aliases: Use short names (FROM users u JOIN transactions t) for readability
    • Multiple joins: You can chain them (users → transactions → categories)

Concepts to learn: GROUP BY + Aggregations
• COUNT(*): Number of rows (includes NULLs)
• COUNT(column): Number of non-NULL values in that column
• SUM(column): Total of numeric column (NULL values ignored)
• AVG(column): Average (NULL values ignored, careful with this)
• MIN/MAX: Smallest/largest value
• GROUP BY: Split data into groups, aggregate each group separately
  - Every column in SELECT must be either in GROUP BY or inside aggregate function
  - GROUP BY goes after WHERE, before HAVING/ORDER BY
• HAVING: Filter groups AFTER aggregation (use WHERE to filter rows BEFORE aggregation)
  - WHERE filters rows, HAVING filters groups — this is critical
  - HAVING COUNT(*) > 5 means "only groups with more than 5 rows"
• Multiple aggregations: SELECT category, SUM(amount), AVG(amount), COUNT(*) GROUP BY category

## Statistical Insights

- Mean vs Median:
  If mean is much higher than median → data is skewed by large transactions

- Standard Deviation:
  Measures how spread out transactions are

- Range:
  Difference between largest and smallest transaction

- Outliers:
  Extreme values that distort averages

## Key Insight

SQL is not just for retrieving data.
It is used to understand patterns, detect anomalies, and support decisions.