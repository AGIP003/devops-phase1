import { PieChart, Pie, Cell, Tooltip, Legend, ResponsiveContainer } from 'recharts'; 

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
    

    return (
        //ResponsiveContainer wraps every Recharts chart. Avoids it having fixed pixel size and breaking on mobile.
        //Cell gives each pie slice its own colors array
        //Toolformatter shows what appears when you hover over a slice. Without it shows raw numbers
        <ResponsiveContainer width="100%" height={315}>
            <PieChart margin={{ top: 70, right: 28, bottom: 4, left: 8 }}>
                <Pie
                    data={categoryData}
                    dataKey="value"
                    nameKey="name"
                    cx="50%"
                    cy="50%"
                    outerRadius={110}
                    label={({ name, percent }) => 
                    `${name} ${(percent * 100).toFixed(0)}%`
                    }
                   > 
                    {categoryData.map((_, index) => (
                        <Cell key={index} fill={COLORS[index % COLORS.length]} />

                    ))}
                </Pie>
                <Tooltip formatter={(value) => `KES ${value.toLocaleString()}`} />
                <Legend wrapperStyle={{ transform: 'translateY(100px)', paddingTop: '1px' }} />
            </PieChart>
        </ResponsiveContainer>
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
