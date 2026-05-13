import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer } from 'recharts'; 

const COLORS = ['#3b82f6', '#10b981', '#ef4444', '#8b5cf6', '#06b6d4', '#b84fc2', 'rgba(81, 14, 24, 0.66)', '#a4af42'];

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

function ChartsSection({ transactions, filterType }) {
  if (transactions.length === 0) return null;
  

  return (
    <div className="charts-grid">
      <div className="chart-card">
        <h3>Spending by Category</h3>
        <CategoryPieChart transactions={transactions} filterType={filterType}/>
      </div>
      {/* Bar chart will come later */}
    </div>
  );
}

export default ChartsSection;
