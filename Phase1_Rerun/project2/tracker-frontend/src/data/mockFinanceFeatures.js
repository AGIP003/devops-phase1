export const savingsGoals = [
  {
    id: 1,
    name: "iPhone 17 Pro Max",
    targetAmount: 250000,
    savedAmount: 42000,
    monthlyTarget: 28000,
    deadline: "2026-12-15",
    color: "#6f7f3f",
  },
  {
    id: 2,
    name: "Emergency Fund",
    targetAmount: 150000,
    savedAmount: 78000,
    monthlyTarget: 18000,
    deadline: "2026-10-01",
    color: "#2f8f5b",
  },
  {
    id: 3,
    name: "December Trip",
    targetAmount: 90000,
    savedAmount: 21000,
    monthlyTarget: 12000,
    deadline: "2026-11-20",
    color: "#3b82f6",
  },
];

export const debts = [
  {
    id: 1,
    name: "KCB personal loan",
    type: "Bank",
    direction: "i_owe",
    originalAmount: 180000,
    balance: 124000,
    paidAmount: 56000,
    dueDate: "2026-08-30",
    repaymentLabel: "Monthly repayment",
  },
  {
    id: 2,
    name: "Lipa Polepole phone",
    type: "Lipa Polepole",
    direction: "i_owe",
    originalAmount: 65000,
    balance: 27000,
    paidAmount: 38000,
    dueDate: "2026-07-18",
    repaymentLabel: "Weekly repayment",
  },
  {
    id: 3,
    name: "Amina lunch advance",
    type: "Person",
    direction: "owed_to_me",
    originalAmount: 8500,
    balance: 8500,
    paidAmount: 0,
    dueDate: "2026-07-05",
    repaymentLabel: "Friendly reminder",
  },
  {
    id: 4,
    name: "SACCO development loan",
    type: "SACCO",
    direction: "i_owe",
    originalAmount: 90000,
    balance: 54000,
    paidAmount: 36000,
    dueDate: "2026-09-12",
    repaymentLabel: "Monthly repayment",
  },
  {
    id: 5,
    name: "Brian rent split",
    type: "Person",
    direction: "owed_to_me",
    originalAmount: 22000,
    balance: 12000,
    paidAmount: 10000,
    dueDate: "2026-06-30",
    repaymentLabel: "Partly paid",
  },
];

export const subscriptions = [
  {
    id: 1,
    name: "Netflix",
    category: "Streaming",
    amount: 1490,
    dueDate: "2026-06-28",
    billingCycle: "Monthly",
    iconLabel: "N",
    brandColor: "#111111",
    accentColor: "#e50914",
  },
  {
    id: 2,
    name: "Spotify",
    category: "Music",
    amount: 490,
    dueDate: "2026-07-02",
    billingCycle: "Monthly",
    iconLabel: "S",
    brandColor: "#1db954",
    accentColor: "#ffffff",
  },
  {
    id: 3,
    name: "WiFi",
    category: "Internet",
    amount: 3990,
    dueDate: "2026-07-06",
    billingCycle: "Monthly",
    iconLabel: "W",
    brandColor: "#ef4444",
    accentColor: "#ffffff",
  },
  {
    id: 4,
    name: "Electricity",
    category: "Utilities",
    amount: 1265,
    dueDate: "2026-07-15",
    billingCycle: "Monthly",
    iconLabel: "E",
    brandColor: "#e8eef9",
    accentColor: "#3b5ba9",
  },
  {
    id: 5,
    name: "Figma",
    category: "Design",
    amount: 3999,
    dueDate: "2026-08-01",
    billingCycle: "Monthly",
    iconLabel: "F",
    brandColor: "#2f243a",
    accentColor: "#a259ff",
  },
];

export const quotationProjects = [
  {
    id: 1,
    title: "Warehouse shelving",
    category: "Hardware",
    status: "Comparing",
    items: [
      { id: "steel-posts", name: "Steel posts", quantity: 24, unit: "pcs" },
      { id: "plywood", name: "18mm plywood boards", quantity: 16, unit: "boards" },
      { id: "bolts", name: "Anchor bolts", quantity: 120, unit: "pcs" },
    ],
    quotations: [
      {
        id: 1,
        supplier: "Kamau Hardware",
        contact: "Industrial Area",
        validUntil: "2026-07-10",
        items: {
          "steel-posts": { unitPrice: 1850 },
          plywood: { unitPrice: 3200 },
          bolts: { unitPrice: 45 },
        },
      },
      {
        id: 2,
        supplier: "Metro Steel Yard",
        contact: "Mombasa Road",
        validUntil: "2026-07-08",
        items: {
          "steel-posts": { unitPrice: 1720 },
          plywood: { unitPrice: 3400 },
          bolts: { unitPrice: 42 },
        },
      },
      {
        id: 3,
        supplier: "Jenga Supplies",
        contact: "Ruiru",
        validUntil: "2026-07-15",
        items: {
          "steel-posts": { unitPrice: 1900 },
          plywood: { unitPrice: 3050 },
          bolts: { unitPrice: 48 },
        },
      },
    ],
  },
  {
    id: 2,
    title: "Rental unit paintwork",
    category: "Fundi",
    status: "Ready to print",
    items: [
      { id: "paint", name: "Paint", quantity: 12, unit: "litres" },
      { id: "labour", name: "Labour", quantity: 4, unit: "days" },
      { id: "brushes", name: "Brushes and rollers", quantity: 1, unit: "set" },
    ],
    quotations: [
      {
        id: 1,
        supplier: "Otieno & Sons",
        contact: "Site visit done",
        validUntil: "2026-07-02",
        items: {
          paint: { unitPrice: 850 },
          labour: { unitPrice: 2500 },
          brushes: { unitPrice: 1800 },
        },
      },
      {
        id: 2,
        supplier: "QuickBrush Crew",
        contact: "WhatsApp quote",
        validUntil: "2026-07-01",
        items: {
          paint: { unitPrice: 900 },
          labour: { unitPrice: 2200 },
          brushes: { unitPrice: 2100 },
        },
      },
    ],
  },
];

export const budgets = [
  {
    id: 1,
    name: "Monthly supermarket run",
    category: "Shopping",
    targetAmount: 18500,
    lastSpend: 20100,
    items: [
      { id: 1, name: "Rice 10kg", estimatedAmount: 2400, checked: true },
      { id: 2, name: "Cooking oil", estimatedAmount: 1850, checked: true },
      { id: 3, name: "Milk carton", estimatedAmount: 720, checked: false },
      { id: 4, name: "Vegetables", estimatedAmount: 1600, checked: false },
      { id: 5, name: "Cleaning supplies", estimatedAmount: 2200, checked: false },
    ],
  },
  {
    id: 2,
    name: "Site lunch supplies",
    category: "Work",
    targetAmount: 7200,
    lastSpend: 6900,
    items: [
      { id: 1, name: "Tea leaves", estimatedAmount: 450, checked: true },
      { id: 2, name: "Sugar", estimatedAmount: 680, checked: false },
      { id: 3, name: "Bread", estimatedAmount: 900, checked: false },
      { id: 4, name: "Disposable cups", estimatedAmount: 750, checked: true },
    ],
  },
];

export function getSortedSubscriptions(subscriptionList = subscriptions) {
  return [...subscriptionList].sort(
    (a, b) => new Date(a.dueDate).getTime() - new Date(b.dueDate).getTime()
  );
}

export function getQuotationItemTotal(item, quote) {
  return item.quantity * Number(quote.items[item.id]?.unitPrice || 0);
}

export function getQuotationTotal(project, quote) {
  return project.items.reduce((sum, item) => sum + getQuotationItemTotal(item, quote), 0);
}

export function getBudgetTotal(items = []) {
  return items.reduce((sum, item) => sum + Number(item.estimatedAmount || 0), 0);
}

export function getGoalProgress(goal) {
  if (!goal?.targetAmount) return 0;
  return Math.min(100, Math.round((goal.savedAmount / goal.targetAmount) * 100));
}

export function getDebtProgress(debt) {
  if (!debt?.originalAmount) return 0;
  return Math.min(100, Math.round((debt.paidAmount / debt.originalAmount) * 100));
}

export function getDebtSummary(debtList = debts) {
  return debtList.reduce(
    (summary, debt) => {
      if (debt.direction === "i_owe") {
        summary.youOwe += debt.balance;
      }
      if (debt.direction === "owed_to_me") {
        summary.owedToYou += debt.balance;
      }
      summary.netPosition = summary.owedToYou - summary.youOwe;
      return summary;
    },
    { youOwe: 0, owedToYou: 0, netPosition: 0 }
  );
}

export function getDebtChartData(debtList = debts) {
  return debtList.reduce((items, debt) => {
    const existing = items.find((item) => item.name === debt.type);
    if (existing) {
      existing.value += debt.balance;
      return items;
    }
    return [...items, { name: debt.type, value: debt.balance }];
  }, []);
}
