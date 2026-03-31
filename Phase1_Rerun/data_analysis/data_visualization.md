Day 6 — Pandas + Visualization (Matplotlib, Seaborn)

CORE IDEA:
Pandas = SQL in Python + more flexibility.
DataFrame = table
Series = column

SQL → Pandas Mapping:
SELECT * FROM table → df
SELECT col1, col2 → df[['col1', 'col2']]
WHERE amount > 100 → df[df['amount'] > 100]
ORDER BY amount DESC → df.sort_values('amount', ascending=False)
LIMIT 10 → df.head(10)

----------------------------------------
PANDAS FUNDAMENTALS

Viewing Data:
df.head()
df.tail()
df.info()
df.describe()
df.shape

Selecting Data:
df['amount']
df[['amount', 'category']]

Filtering:
df[df['amount'] > 100]

Sorting:
df.sort_values('amount', ascending=False)

New Columns:
df['tax'] = df['amount'] * 0.16

Handling NULLs:
df.isna()
df.dropna()
df.fillna(0)

----------------------------------------
GROUPBY (SQL GROUP BY)

SQL:
SELECT category, SUM(amount)
FROM transactions
GROUP BY category

Pandas:
df.groupby('category')['amount'].sum()

Multiple Aggregations:
df.groupby('category')['amount'].agg(['sum', 'mean', 'count'])

Named Aggregation:
df.groupby('category').agg(
    total=('amount', 'sum'),
    avg=('amount', 'mean')
)

----------------------------------------
MERGE (SQL JOIN)

SQL:
SELECT *
FROM transactions t
LEFT JOIN users u
ON t.user_id = u.id

Pandas:
pd.merge(transactions, users,
         left_on='user_id',
         right_on='id',
         how='left')

JOIN TYPES:
inner → matching only
left → all left + matches
right → all right + matches
outer → everything

----------------------------------------
CONCAT (SQL UNION)

pd.concat([df1, df2])

----------------------------------------
VISUALIZATION

Matplotlib:
plt.plot(x, y) → line chart
plt.bar(x, y) → bar chart
plt.scatter(x, y)

Labels:
plt.xlabel()
plt.ylabel()
plt.title()

Save:
plt.savefig('chart.png')

----------------------------------------
SEABORN (Better Visuals)

Bar Chart:
sns.barplot(data=df, x='category', y='amount', estimator=sum)

Line Plot:
sns.lineplot(data=df, x='date', y='amount')

Box Plot (distribution):
sns.boxplot(data=df, x='category', y='amount')

----------------------------------------
WHEN TO USE WHAT

SQL:
- Filtering large data
- Joins
- Aggregations in DB

Pandas:
- Complex transformations
- Statistical analysis
- Visualization

REAL FLOW:
Database → SQL → Pandas → Charts → Insights