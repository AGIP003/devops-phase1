import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'; 

const COLORS = ['#3b82f6', '#10b981', '#ef4444', '#8b5cf6', '#06b6d4', '#b84fc2', 'rgba(81, 14, 24, 0.66)', '#a4af42'];
const INCOME_COLOR = '#2f8f5b';
const EXPENSE_COLOR = '#3b82f6';
const EXPENSE_WARNING_COLOR = '#c2413b';

function getMonthKey(dateValue) {
  const date = new Date(dateValue);
  if (Number.isNaN(date.getTime())) return null;

  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`;
}

function getMonthLabel(monthKey) {
  const [year, month] = monthKey.split('-').map(Number);
  const date = new Date(year, month - 1, 1);

  return date.toLocaleDateString('en-KE', {
    month: 'short',
    year: '2-digit',
  });
}

function buildMonthlyData(transactions) {
  const monthMap = transactions.reduce((acc, transaction) => {
    const monthKey = getMonthKey(transaction.date);
    if (!monthKey) return acc;

    if (!acc[monthKey]) {
      acc[monthKey] = {
        month: getMonthLabel(monthKey),
        monthKey,
        income: 0,
        expense: 0,
      };
    }

    const amount = Number(transaction.amount || 0);
    if (transaction.type === 'income') {
      acc[monthKey].income += amount;
    }
    if (transaction.type === 'expense') {
      acc[monthKey].expense += amount;
    }

    return acc;
  }, {});

  return Object.values(monthMap).sort((a, b) => a.monthKey.localeCompare(b.monthKey));
}

export function MonthlyTrendChart({ transactions, filterType }) {
  const monthlyData = buildMonthlyData(transactions);
  const showIncome = filterType === 'all' || filterType === 'income';
  const showExpense = filterType === 'all' || filterType === 'expense';

  return (
    <div className="chart-card">
      <div className="chart-card-header">
        <h3>Monthly Trend</h3>
        <span className="chart-card-kicker">
          {filterType === 'all' ? 'Income vs Expense' : filterType}
        </span>
      </div>

      <ResponsiveContainer width="100%" height={260}>
        <BarChart data={monthlyData} margin={{ top: 12, right: 12, bottom: 0, left: 0 }}>
          <CartesianGrid stroke="#edf1e8" vertical={false} />
          <XAxis
            dataKey="month"
            axisLine={false}
            tickLine={false}
            tick={{ fill: '#647067', fontSize: 12, fontWeight: 700 }}
          />
          <YAxis
            axisLine={false}
            tickLine={false}
            tick={{ fill: '#647067', fontSize: 12 }}
            tickFormatter={(value) => `${Math.round(value / 1000)}k`}
            width={42}
          />
          <Tooltip
            cursor={{ fill: 'rgba(111, 127, 63, 0.08)' }}
            formatter={(value, name) => [`KES ${Number(value).toLocaleString('en-KE')}`, name]}
            labelStyle={{ color: '#17211b', fontWeight: 800 }}
          />
          {showIncome && (
            <Bar
              dataKey="income"
              fill={INCOME_COLOR}
              name="Income"
              radius={[8, 8, 0, 0]}
              maxBarSize={34}
            />
          )}
          {showExpense && (
            <Bar
              dataKey="expense"
              name="Expense"
              radius={[8, 8, 0, 0]}
              maxBarSize={34}
            >
              {monthlyData.map((entry) => (
                <Cell
                  key={`expense-${entry.monthKey}`}
                  fill={entry.expense > entry.income ? EXPENSE_WARNING_COLOR : EXPENSE_COLOR}
                />
              ))}
            </Bar>
          )}
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

function CategoryPieChart({ transactions, filterType }) {
    
    const groupBy = filterType === "all" ? "type" : "category";

    const categoryData = transactions.reduce((acc, t) => {
        const name = t[groupBy];
        const existing = acc.find(item => item.name === name);
        const amount = Number(t.amount);
        if (existing) {
            existing.value += amount;
        } else {
            acc.push({ name: name, value:amount });
        }
        return acc;
    }, []);
    
    const chartTotal = categoryData.reduce((sum, item) => sum + item.value, 0);

    return (
        //ResponsiveContainer wraps every Recharts chart. Avoids it having fixed pixel size and breaking on mobile.
        //Cell gives each pie slice its own colors array
        //Toolformatter shows what appears when you hover over a slice. Without it shows raw numbers
        <div className="donut-chart">
            <ResponsiveContainer width="100%" height={240}>
                <PieChart margin={{ top: 10, right: 13, bottom: 4, left: 8 }}>
                    <Pie
                        data={categoryData}
                        dataKey="value"
                        nameKey="name"
                        cx="50%"
                        cy="50%"
                        innerRadius={62}
                        outerRadius={110}
                        paddingAngle={2}
                        cornerRadius={6}
                       > 
                        {categoryData.map((_, index) => (
                            <Cell key={index} fill={COLORS[index % COLORS.length]} />

                        ))}
                    </Pie>
                    <Tooltip formatter={(value) => `KES ${value.toLocaleString()}`} />
                    
                </PieChart>
            </ResponsiveContainer>

            <div className='donut-legend'>
                {categoryData.map((item, index) => {
                const percent = chartTotal ? Math.round((item.value / chartTotal) * 100) : 0;

                return (
                    <div className="donut-legend-item" key={item.name}>
                        <span
                            className="donut-legend-dot"
                            style={{ backgroundColor: COLORS[index % COLORS.length] }}
                        />
                        <span className="donut-legend-name">{item.name}</span>
                        <span className="donut-legend-percent">{percent}%</span>
                    </div>
                );
            })}

            </div>
        </div>
    )
}

function ChartsSection({ transactions, filterType, setFilterType }) {
  if (transactions.length === 0) return null;
  

  return (
    <div className="charts-grid">
      <div className="chart-card">
        <div className="chart-card-header">
          <h3>Spending by Category</h3>
          <select
            className="chart-filter-select"
            value={filterType}
            onChange={(e) => setFilterType(e.target.value)}
            aria-label="Filter chart by transaction type"
          >
            <option value="all">All</option>
            <option value="income">Income</option>
            <option value="expense">Expense</option>
          </select>
        </div>
        <CategoryPieChart transactions={transactions} filterType={filterType}/>
      </div>
      {/* Bar chart will come later */}
    </div>
  );
}

export default ChartsSection;
