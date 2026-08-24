export function getQuoteItemPrice(quote, itemId) {
  const rawPrice = quote?.items?.[itemId]?.unitPrice;
  if (rawPrice === "" || rawPrice === null || rawPrice === undefined) return null;

  const price = Number(rawPrice);
  return Number.isFinite(price) && price >= 0 ? price : null;
}

export function getQuoteItemTotal(item, quote) {
  const unitPrice = getQuoteItemPrice(quote, item.id);
  if (unitPrice === null) return null;
  return Number(item.quantity || 0) * unitPrice;
}

export function getQuoteBreakdown(project, quote) {
  const itemTotals = project.items.map((item) => getQuoteItemTotal(item, quote));
  const pricedItems = itemTotals.filter((value) => value !== null);
  const subtotal = pricedItems.reduce((total, value) => total + value, 0);
  const deliveryCost = Math.max(Number(quote.deliveryCost || 0), 0);
  const discount = Math.max(Number(quote.discount || 0), 0);
  const taxRate = Math.max(Number(quote.taxRate || 0), 0);
  const tax = quote.taxMode === "excluded" ? subtotal * (taxRate / 100) : 0;
  const total = Math.max(subtotal + deliveryCost + tax - discount, 0);
  const itemCount = project.items.length;
  const pricedItemCount = pricedItems.length;

  return {
    complete: itemCount > 0 && pricedItemCount === itemCount,
    coverage: itemCount ? Math.round((pricedItemCount / itemCount) * 100) : 0,
    deliveryCost,
    discount,
    itemCount,
    pricedItemCount,
    subtotal,
    tax,
    total,
  };
}

export function getCompleteQuoteRankings(project) {
  return project.quotations
    .map((quote) => ({
      quote,
      breakdown: quote.breakdown || getQuoteBreakdown(project, quote),
    }))
    .filter(({ breakdown }) => breakdown.complete)
    .sort(
      (left, right) => Number(left.breakdown.total) - Number(right.breakdown.total),
    );
}

export function getItemLowestPrice(project, itemId) {
  const prices = project.quotations
    .map((quote) => getQuoteItemPrice(quote, itemId))
    .filter((price) => price !== null);
  return prices.length ? Math.min(...prices) : null;
}

export function normalizeQuotationProjects(projects) {
  return projects.map((project) => ({
    ...project,
    preferredQuoteId: project.preferredQuoteId ?? null,
    notes: project.notes || "",
    quotations: project.quotations.map((quote, index) => ({
      ...quote,
      items: Object.fromEntries(
        (quote.prices || []).map((price) => [
          price.itemId,
          { unitPrice: price.unitPrice },
        ]),
      ),
      deliveryCost: quote.deliveryCost ?? 0,
      deliveryDays: quote.deliveryDays ?? index + 2,
      discount: quote.discount ?? 0,
      paymentTerms: quote.paymentTerms || "Payment on delivery",
      taxMode: quote.taxMode || "included",
      taxRate: quote.taxRate ?? 16,
    })),
  }));
}
