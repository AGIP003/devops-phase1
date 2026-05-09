import { PieChart, Pie, Cell, Tooltip, Legend, ResponsiveContainer } from 'recharts'; 

const COLORS = ['#3b82f6', '#10b981', '#ef4444', '#8b5cf6', '#06b6d4', '#c32dd1', '#d675'];

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
        <ResponsiveContainer width="100%" height={300}>
            <PieChart>
                <Pie
                    data={categoryData}
                    dataKey="value"
                    nameKey="name"
                    cx="50%"
                    cy="50%"
                    outerRadius={100}
                    label={({ name, percent }) => 
                    `${name} ${(percent * 100).toFixed(0)}%`
                    }
                   > 
                    {categoryData.map((_, index) => (
                        <Cell key={index} fill={COLORS[index % COLORS.length]} />

                    ))}
                </Pie>
                <Tooltip formatter={(value) => `KES ${value.toLocaleString()}`} />
                <Legend />
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