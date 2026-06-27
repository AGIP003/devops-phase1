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

export const chamaGroups = [
  {
    id: 1,
    name: "Kilifi Sisters Merry-Go-Round",
    type: "Merry-go-round",
    monthlyContribution: 5000,
    dueDate: "2026-07-05",
    currentRecipient: "Amina W.",
    nextRecipient: "Mercy K.",
    status: "Collecting",
    paidCount: 8,
    memberCount: 10,
    poolAmount: 40000,
    targetAmount: 50000,
    paybillMode: "Tracking only",
    members: [
      { id: 1, name: "Amina W.", status: "paid", strikes: 0 },
      { id: 2, name: "Mercy K.", status: "paid", strikes: 0 },
      { id: 3, name: "Jay M.", status: "paid", strikes: 0 },
      { id: 4, name: "Njeri K.", status: "paid", strikes: 1 },
      { id: 5, name: "Faith O.", status: "pending", strikes: 0 },
      { id: 6, name: "Brenda A.", status: "pending", strikes: 1 },
    ],
    votes: [
      { name: "Amina W.", votes: 5 },
      { name: "Mercy K.", votes: 3 },
      { name: "Njeri K.", votes: 2 },
    ],
  },
  {
    id: 2,
    name: "Builders Hardware Chama",
    type: "Investment chama",
    monthlyContribution: 12000,
    dueDate: "2026-07-10",
    currentRecipient: "MMF deposit",
    nextRecipient: "NSE basket",
    status: "Voting",
    paidCount: 6,
    memberCount: 8,
    poolAmount: 72000,
    targetAmount: 96000,
    paybillMode: "Escrow later",
    members: [
      { id: 1, name: "Mwangi", status: "paid", strikes: 0 },
      { id: 2, name: "Otieno", status: "paid", strikes: 0 },
      { id: 3, name: "Kariuki", status: "pending", strikes: 2 },
      { id: 4, name: "Wanjiru", status: "paid", strikes: 0 },
    ],
    votes: [
      { name: "MMF deposit", votes: 4 },
      { name: "NSE basket", votes: 2 },
      { name: "Hold cash", votes: 1 },
    ],
  },
];

export const feeProviders = [
  {
    id: "m-pesa",
    name: "M-Pesa",
    tone: "#2f8f5b",
    helper: "Estimated send/paybill bands",
    bands: [
      { min: 0, max: 100, fee: 0 },
      { min: 101, max: 500, fee: 7 },
      { min: 501, max: 1000, fee: 13 },
      { min: 1001, max: 2500, fee: 23 },
      { min: 2501, max: 5000, fee: 33 },
      { min: 5001, max: 10000, fee: 57 },
      { min: 10001, max: Infinity, fee: 108 },
    ],
  },
  {
    id: "airtel money",
    name: "Airtel Money",
    tone: "#ef4444",
    helper: "Estimated wallet transfer",
    bands: [
      { min: 0, max: 100, fee: 0 },
      { min: 101, max: 500, fee: 6 },
      { min: 501, max: 1000, fee: 11 },
      { min: 1001, max: 2500, fee: 20 },
      { min: 2501, max: 5000, fee: 30 },
      { min: 5001, max: Infinity, fee: 55 },
    ],
  },
  {
    id: "bank transfer",
    name: "Bank",
    tone: "#3b82f6",
    helper: "Estimated mobile banking charge",
    flatFee: 45,
  },
  {
    id: "ipay",
    name: "iPay",
    tone: "#8b5cf6",
    helper: "Estimated checkout processing",
    percent: 1.8,
    minimumFee: 15,
  },
  {
    id: "pesapal",
    name: "Pesapal",
    tone: "#f59e0b",
    helper: "Estimated card/wallet processing",
    percent: 2.1,
    minimumFee: 20,
  },
];

export const feeEvents = [
  { id: 1, description: "Groceries paybill", provider: "m-pesa", amount: 1680, fee: 23, date: "2026-06-27" },
  { id: 2, description: "Rent transfer", provider: "bank transfer", amount: 25000, fee: 45, date: "2026-06-26" },
  { id: 3, description: "Airtime top up", provider: "airtel money", amount: 250, fee: 6, date: "2026-06-25" },
  { id: 4, description: "Online order", provider: "pesapal", amount: 4200, fee: 88, date: "2026-06-22" },
  { id: 5, description: "Client invoice checkout", provider: "ipay", amount: 7600, fee: 137, date: "2026-06-18" },
  { id: 6, description: "Fuel station", provider: "m-pesa", amount: 3200, fee: 33, date: "2026-06-16" },
  { id: 7, description: "School supplies", provider: "m-pesa", amount: 940, fee: 13, date: "2026-06-13" },
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

export function getChamaProgress(chama) {
  return Math.min(100, Math.round((chama.paidCount / Math.max(chama.memberCount, 1)) * 100));
}

export function normalizeFeeProvider(paymentMethod = "") {
  const cleanMethod = paymentMethod.toLowerCase().trim();
  if (cleanMethod.includes("m-pesa") || cleanMethod.includes("mpesa")) return "m-pesa";
  if (cleanMethod.includes("airtel")) return "airtel money";
  if (cleanMethod.includes("bank")) return "bank transfer";
  if (cleanMethod.includes("ipay")) return "ipay";
  if (cleanMethod.includes("pesapal")) return "pesapal";
  return cleanMethod;
}

export function getFeeProvider(paymentMethod = "") {
  const providerId = normalizeFeeProvider(paymentMethod);
  return feeProviders.find((provider) => provider.id === providerId);
}

export function calculateTransactionFee(paymentMethod, amount) {
  const provider = getFeeProvider(paymentMethod);
  const value = Number(amount || 0);
  if (!provider || value <= 0) return { fee: 0, provider: null, supported: false };

  if (provider.bands) {
    const band = provider.bands.find((item) => value >= item.min && value <= item.max);
    return { fee: band?.fee || 0, provider, supported: true };
  }

  if (provider.percent) {
    const fee = Math.max(provider.minimumFee || 0, Math.round(value * (provider.percent / 100)));
    return { fee, provider, supported: true };
  }

  return { fee: provider.flatFee || 0, provider, supported: true };
}

export function getFeeSummary(events = feeEvents) {
  const now = new Date("2026-06-27T12:00:00");
  const weekStart = new Date(now);
  weekStart.setDate(now.getDate() - 6);
  const monthStart = new Date(now.getFullYear(), now.getMonth(), 1);

  const totalWeek = events
    .filter((event) => new Date(event.date) >= weekStart)
    .reduce((sum, event) => sum + event.fee, 0);

  const totalMonth = events
    .filter((event) => new Date(event.date) >= monthStart)
    .reduce((sum, event) => sum + event.fee, 0);

  const providerTotals = feeProviders.map((provider) => {
    const total = events
      .filter((event) => normalizeFeeProvider(event.provider) === provider.id)
      .reduce((sum, event) => sum + event.fee, 0);
    return { ...provider, total };
  }).sort((a, b) => b.total - a.total);

  return {
    totalWeek,
    totalMonth,
    providerTotals,
    highestProvider: providerTotals[0],
  };
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
