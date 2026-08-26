import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Check, ChevronDown, CircleAlert, Clock3, Pencil, Plus, Search, Trash2, Truck, X } from "lucide-react";
import toast from "react-hot-toast";

import { useAdjustedCurrency } from "../hooks/useAdjustedCurrency";
import api from "../services/api";
import {
  getCompleteQuoteRankings,
  getItemLowestPrice,
  getQuoteItemPrice,
  getQuoteItemTotal,
  normalizeQuotationProjects,
} from "../utils/quotations";

const dateFormatter = new Intl.DateTimeFormat("en-KE", { day: "2-digit", month: "short", year: "numeric" });
const emptyProject = { title: "", category: "", notes: "" };
const unitGroups = [
  ["Count", [["pcs", "Pieces (pcs)"], ["packets", "Packets"], ["boxes", "Boxes"], ["cartons", "Cartons"], ["sets", "Sets"], ["pairs", "Pairs"], ["dozens", "Dozens"]]],
  ["Weight", [["g", "Grams (g)"], ["kg", "Kilograms (kg)"], ["tonnes", "Tonnes"]]],
  ["Volume", [["ml", "Millilitres (ml)"], ["litres", "Litres"], ["m3", "Cubic metres (m³)"]]],
  ["Length and area", [["cm", "Centimetres (cm)"], ["metres", "Metres"], ["sqm", "Square metres (m²)"], ["feet", "Feet"]]],
  ["Work and services", [["hours", "Hours"], ["days", "Days"], ["jobs", "Jobs"], ["visits", "Visits"]]],
  ["Construction and supplies", [["bags", "Bags"], ["rolls", "Rolls"], ["sheets", "Sheets"], ["bundles", "Bundles"], ["loads", "Loads"]]],
];
const knownUnits = new Set(unitGroups.flatMap(([, units]) => units.map(([value]) => value)));

function newQuoteForm(items = []) {
  return {
    supplier: "", contact: "", validUntil: "", deliveryCost: "0", discount: "0",
    taxMode: "included", taxRate: "16", deliveryDays: "", paymentTerms: "",
    prices: Object.fromEntries(items.map((item) => [item.id, ""])),
  };
}

function quoteToForm(quote, items) {
  const form = newQuoteForm(items);
  quote.prices.forEach((price) => { form.prices[price.itemId] = price.unitPrice; });
  return {
    ...form, supplier: quote.supplier, contact: quote.contact || "", validUntil: quote.validUntil || "",
    deliveryCost: quote.deliveryCost, discount: quote.discount, taxMode: quote.taxMode,
    taxRate: quote.taxRate, deliveryDays: quote.deliveryDays ?? "", paymentTerms: quote.paymentTerms || "",
  };
}

function quotePayload(form) {
  return {
    ...form,
    contact: form.contact.trim() || null,
    deliveryDays: form.deliveryDays === "" ? null : Number(form.deliveryDays),
    paymentTerms: form.paymentTerms.trim() || null,
    prices: Object.entries(form.prices)
      .filter(([, price]) => price !== "")
      .map(([itemId, unitPrice]) => ({ itemId: Number(itemId), unitPrice })),
  };
}

function formatDate(value) { return value ? dateFormatter.format(new Date(`${value}T00:00:00`)) : "Not stated"; }
function daysUntil(value) {
  if (!value) return null;
  const today = new Date(); today.setHours(0, 0, 0, 0);
  return Math.ceil((new Date(`${value}T00:00:00`) - today) / 86_400_000);
}

function Field({ label, children, wide = false }) {
  return <label className={`quote-field${wide ? " quote-field-wide" : ""}`}><span>{label}</span>{children}</label>;
}

function EditorHeading({ eyebrow, title, onClose }) {
  return <div className="quote-editor-heading"><div><small>{eyebrow}</small><h2>{title}</h2></div><button type="button" className="quote-icon-button" onClick={onClose} aria-label="Close form"><X size={18} /></button></div>;
}

function ProjectForm({ initial = emptyProject, saving, onCancel, onSubmit }) {
  const [form, setForm] = useState(initial);
  return <form className="quote-editor" onSubmit={(event) => { event.preventDefault(); onSubmit(form); }}>
    <EditorHeading eyebrow="Purchase workspace" title={initial.id ? "Edit comparison" : "Start a comparison"} onClose={onCancel} />
    <div className="quote-form-grid">
      <Field label="What are you buying?"><input required maxLength={100} value={form.title} onChange={(event) => setForm({ ...form, title: event.target.value })} placeholder="Office chairs" /></Field>
      <Field label="Category"><input required maxLength={50} value={form.category} onChange={(event) => setForm({ ...form, category: event.target.value })} placeholder="Equipment" /></Field>
      <Field label="Decision notes" wide><textarea maxLength={300} value={form.notes || ""} onChange={(event) => setForm({ ...form, notes: event.target.value })} placeholder="Requirements that should influence the choice" /></Field>
    </div>
    <div className="quote-form-actions"><button type="button" className="quote-secondary-button" onClick={onCancel}>Cancel</button><button className="feature-primary-button" disabled={saving}>{saving ? "Saving…" : "Save comparison"}</button></div>
  </form>;
}

function ItemForm({ initialItem = null, saving, onCancel, onSubmit }) {
  const initialUnit = initialItem?.unit || "pcs";
  const [form, setForm] = useState({
    name: initialItem?.name || "",
    quantity: initialItem?.quantity || "1",
    unit: knownUnits.has(initialUnit) ? initialUnit : "custom",
  });
  const [customUnit, setCustomUnit] = useState(knownUnits.has(initialUnit) ? "" : initialUnit);
  return <form className="quote-editor quote-compact-editor" onSubmit={(event) => { event.preventDefault(); onSubmit({ ...form, unit: form.unit === "custom" ? customUnit : form.unit }); }}>
    <EditorHeading eyebrow="Requested item" title={initialItem ? `Edit ${initialItem.name}` : "Add the same requirement for every supplier"} onClose={onCancel} />
    <div className="quote-form-grid quote-item-form-grid">
      <Field label="Item"><input required maxLength={100} value={form.name} onChange={(event) => setForm({ ...form, name: event.target.value })} placeholder="Ergonomic chair" /></Field>
      <Field label="Quantity"><input required min="0.01" step="0.01" type="number" value={form.quantity} onChange={(event) => setForm({ ...form, quantity: event.target.value })} /></Field>
      <Field label="Unit"><select required value={form.unit} onChange={(event) => setForm({ ...form, unit: event.target.value })}>{unitGroups.map(([group, units]) => <optgroup key={group} label={group}>{units.map(([value, label]) => <option key={value} value={value}>{label}</option>)}</optgroup>)}<option value="custom">Custom unit…</option></select></Field>
      {form.unit === "custom" && <Field label="Custom unit"><input required autoFocus maxLength={30} value={customUnit} onChange={(event) => setCustomUnit(event.target.value)} placeholder="For example, trays" /></Field>}
    </div>
    <div className="quote-form-actions"><button type="button" className="quote-secondary-button" onClick={onCancel}>Cancel</button><button className="feature-primary-button" disabled={saving}>{saving ? "Saving…" : initialItem ? "Update item" : "Add item"}</button></div>
  </form>;
}

function ItemSupplierPriceForm({ item, quotations, saving, onCancel, onSubmit }) {
  const [prices, setPrices] = useState(() => Object.fromEntries(
    quotations.map((quote) => [quote.id, getQuoteItemPrice(quote, item.id) ?? ""]),
  ));

  return <form className="quote-editor quote-item-price-editor" onSubmit={(event) => {
    event.preventDefault();
    onSubmit({
      prices: quotations.map((quote) => ({
        quotationId: quote.id,
        unitPrice: prices[quote.id] === "" ? null : prices[quote.id],
      })),
    });
  }}>
    <EditorHeading eyebrow="Keep the comparison complete" title={`Add ${item.name} prices`} onClose={onCancel} />
    <p className="quote-editor-intro">The item is already on the shared list. Add each supplier’s unit price here instead of reopening every quotation.</p>
    <div className="quote-price-entry quote-supplier-price-grid">
      {quotations.map((quote) => <label key={quote.id} className="quote-price-row">
        <span><strong>{quote.supplier}</strong><small>{item.quantity} {item.unit} requested</small></span>
        <span className="quote-money-input"><small>KES</small><input min="0" step="0.01" type="number" value={prices[quote.id]} onChange={(event) => setPrices((current) => ({ ...current, [quote.id]: event.target.value }))} aria-label={`${quote.supplier} unit price for ${item.name}`} placeholder="Not quoted" /></span>
      </label>)}
    </div>
    <p className="quote-form-note">Leave a price empty if that supplier did not quote this item. Their offer will remain clearly marked incomplete.</p>
    <div className="quote-form-actions"><button type="button" className="quote-secondary-button" onClick={onCancel}>Do this later</button><button className="feature-primary-button" disabled={saving}>{saving ? "Saving…" : "Save supplier prices"}</button></div>
  </form>;
}

function SupplierForm({ items, initialQuote, saving, onCancel, onSubmit }) {
  const [form, setForm] = useState(() => initialQuote ? quoteToForm(initialQuote, items) : newQuoteForm(items));
  const [showDetails, setShowDetails] = useState(Boolean(initialQuote));
  const setValue = (key, value) => setForm((current) => ({ ...current, [key]: value }));
  return <form className="quote-editor quote-supplier-editor" onSubmit={(event) => { event.preventDefault(); onSubmit(quotePayload(form)); }}>
    <EditorHeading eyebrow="Supplier offer" title={initialQuote ? `Edit ${initialQuote.supplier}` : "Add a supplier quotation"} onClose={onCancel} />
    <div className="quote-form-grid">
      <Field label="Supplier"><input required maxLength={100} value={form.supplier} onChange={(event) => setValue("supplier", event.target.value)} placeholder="Business name" /></Field>
      <Field label="Contact"><input maxLength={100} value={form.contact} onChange={(event) => setValue("contact", event.target.value)} placeholder="Phone or email (optional)" /></Field>
      <Field label="Valid until (optional)"><input type="date" value={form.validUntil} onChange={(event) => setValue("validUntil", event.target.value)} /></Field>
    </div>
    <div className="quote-price-entry"><div><h3>Item prices</h3><p>Leave an item empty when the supplier did not quote it. The offer will be marked incomplete.</p></div>
      {items.map((item) => <label key={item.id} className="quote-price-row"><span><strong>{item.name}</strong><small>{item.quantity} {item.unit}</small></span><span className="quote-money-input"><small>KES</small><input min="0" step="0.01" type="number" value={form.prices[item.id] ?? ""} onChange={(event) => setForm((current) => ({ ...current, prices: { ...current.prices, [item.id]: event.target.value } }))} aria-label={`${item.name} unit price`} placeholder="Unit price" /></span></label>)}
    </div>
    <button type="button" className={`quote-details-toggle${showDetails ? " is-open" : ""}`} aria-expanded={showDetails} onClick={() => setShowDetails((visible) => !visible)}><span className="quote-details-icon"><Truck size={18} /></span><span><strong>{showDetails ? "Optional quotation details" : "Add delivery and other costs"}</strong><small>Delivery, discounts, tax and payment terms</small></span><ChevronDown size={18} className="quote-details-chevron" /></button>
    {showDetails && <div className="quote-form-grid quote-cost-grid quote-advanced-fields">
      <Field label="Delivery time (days)"><input min="0" step="1" type="number" value={form.deliveryDays} onChange={(event) => setValue("deliveryDays", event.target.value)} placeholder="Optional" /></Field>
      <Field label="Delivery cost"><input min="0" step="0.01" type="number" value={form.deliveryCost} onChange={(event) => setValue("deliveryCost", event.target.value)} /></Field>
      <Field label="Discount"><input min="0" step="0.01" type="number" value={form.discount} onChange={(event) => setValue("discount", event.target.value)} /></Field>
      <Field label="Tax treatment"><select value={form.taxMode} onChange={(event) => setValue("taxMode", event.target.value)}><option value="included">Tax included</option><option value="excluded">Tax added separately</option><option value="none">No tax</option></select></Field>
      {form.taxMode === "excluded" && <Field label="Tax rate (%)"><input min="0" max="100" step="0.01" type="number" value={form.taxRate} onChange={(event) => setValue("taxRate", event.target.value)} /></Field>}
      <Field label="Payment terms" wide><input maxLength={150} value={form.paymentTerms} onChange={(event) => setValue("paymentTerms", event.target.value)} placeholder="For example, 50% deposit" /></Field>
    </div>}
    <div className="quote-form-actions"><button type="button" className="quote-secondary-button" onClick={onCancel}>Cancel</button><button className="feature-primary-button" disabled={saving}>{saving ? "Saving…" : initialQuote ? "Update quotation" : "Save quotation"}</button></div>
  </form>;
}

function QuoteCard({ quote, lowestId, formatCurrency, saving, onEdit, onDelete, onPrefer }) {
  const validityDays = daysUntil(quote.validUntil);
  const expired = validityDays !== null && validityDays < 0;
  return <article className={`quote-offer-card${quote.preferred ? " is-preferred" : ""}`}>
    <div className="quote-offer-topline"><div><h3>{quote.supplier}</h3><p>{quote.contact || "No supplier contact saved"}</p></div><div className="quote-badges">
      {quote.id === lowestId && <span className="quote-badge quote-badge-lowest">Lowest cost</span>}
      {quote.preferred && <span className="quote-badge quote-badge-preferred"><Check size={13} /> Preferred</span>}
      {!quote.breakdown.complete && <span className="quote-badge quote-badge-warning">{quote.breakdown.coverage}% priced</span>}
    </div></div>
    <strong className="quote-offer-total">{formatCurrency(Number(quote.breakdown.total))}</strong><span className="quote-total-caption">landed total {quote.breakdown.complete ? "" : "so far"}</span>
    <dl className="quote-offer-facts">
      <div><dt><Truck size={15} /> Delivery</dt><dd>{quote.deliveryDays === null ? "Not stated" : `${quote.deliveryDays} days`}</dd></div>
      <div><dt><Clock3 size={15} /> Validity</dt><dd className={expired ? "is-expired" : ""}>{quote.validUntil ? expired ? `Expired ${formatDate(quote.validUntil)}` : `Until ${formatDate(quote.validUntil)}` : "Not stated"}</dd></div>
      <div><dt>Tax</dt><dd>{quote.taxMode === "excluded" ? `${quote.taxRate}% added` : quote.taxMode === "included" ? "Included" : "Not charged"}</dd></div>
      <div><dt>Terms</dt><dd>{quote.paymentTerms || "Not stated"}</dd></div>
    </dl>
    <div className="quote-card-actions"><button type="button" className="quote-text-button" onClick={() => onPrefer(quote)} disabled={saving}>{quote.preferred ? "Remove choice" : "Choose supplier"}</button><button type="button" className="quote-icon-button" onClick={() => onEdit(quote)} aria-label={`Edit ${quote.supplier}`}><Pencil size={16} /></button><button type="button" className="quote-icon-button quote-danger-button" onClick={() => onDelete(quote)} aria-label={`Delete ${quote.supplier}`}><Trash2 size={16} /></button></div>
  </article>;
}

function DesktopComparison({ project, lowestId, formatCurrency }) {
  return <div className="quote-desktop-comparison quote-table-wrap"><table className="quote-table">
    <thead><tr><th className="quote-sticky-cell">Requested item</th><th>Qty</th>{project.quotations.map((quote) => <th key={quote.id}><span>{quote.supplier}</span>{quote.id === lowestId && <small className="quote-lowest-label">Lowest complete cost</small>}</th>)}</tr></thead>
    <tbody>{project.items.map((item) => { const lowest = getItemLowestPrice(project, item.id); return <tr key={item.id}><td className="quote-sticky-cell"><strong>{item.name}</strong><small>{item.unit}</small></td><td>{item.quantity}</td>{project.quotations.map((quote) => { const unit = getQuoteItemPrice(quote, item.id); return <td key={quote.id} className={unit !== null && unit === lowest ? "quote-best-item" : ""}>{unit === null ? <span className="quote-missing-price">Not supplied</span> : <><span>{formatCurrency(getQuoteItemTotal(item, quote))}</span><small>{formatCurrency(unit)} each</small></>}</td>; })}</tr>; })}</tbody>
    <tfoot><tr><td className="quote-sticky-cell">Landed total</td><td />{project.quotations.map((quote) => <td key={quote.id} className={quote.id === lowestId ? "best-quote" : ""}><strong>{formatCurrency(Number(quote.breakdown.total))}</strong><small>{quote.breakdown.complete ? "Complete offer" : `${quote.breakdown.coverage}% priced`}</small></td>)}</tr></tfoot>
  </table></div>;
}

function MobileComparison({ project, formatCurrency }) {
  const [selected, setSelected] = useState(() => project.quotations.slice(0, 2).map((quote) => quote.id));
  useEffect(() => {
    setSelected(project.quotations.slice(0, 2).map((quote) => quote.id));
  }, [project.id, project.quotations]);
  const visible = selected.map((id) => project.quotations.find((quote) => quote.id === id)).filter(Boolean);
  const slots = Math.min(2, project.quotations.length);
  return <div className="quote-mobile-comparison"><div className="quote-mobile-selectors">{Array.from({ length: slots }, (_, slot) => <label key={slot}><span>{slot ? "Supplier B" : "Supplier A"}</span><select value={selected[slot] || ""} onChange={(event) => setSelected((current) => { const next = [...current]; next[slot] = Number(event.target.value); return next; })}>{project.quotations.map((quote) => <option key={quote.id} value={quote.id}>{quote.supplier}</option>)}</select></label>)}</div>
    <div className="quote-mobile-items">{project.items.map((item) => <article key={item.id}><header><strong>{item.name}</strong><span>{item.quantity} {item.unit}</span></header><div>{visible.map((quote) => { const unit = getQuoteItemPrice(quote, item.id); return <section key={quote.id}><small>{quote.supplier}</small>{unit === null ? <span className="quote-missing-price">Not supplied</span> : <><strong>{formatCurrency(getQuoteItemTotal(item, quote))}</strong><span>{formatCurrency(unit)} each</span></>}</section>; })}</div></article>)}</div>
  </div>;
}

function Quotations() {
  const { formatCurrency } = useAdjustedCurrency();
  const [projects, setProjects] = useState([]);
  const [selectedId, setSelectedId] = useState(null);
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [panel, setPanel] = useState(null);
  const [editingItem, setEditingItem] = useState(null);
  const [pricingItemId, setPricingItemId] = useState(null);
  const [editingQuote, setEditingQuote] = useState(null);
  const activeFormRef = useRef(null);

  const fetchProjects = useCallback(async () => {
    setLoading(true); setError("");
    try {
      const response = await api.get("/quotation-projects");
      const loaded = normalizeQuotationProjects(Array.isArray(response.data) ? response.data : []);
      setProjects(loaded); setSelectedId((current) => current ?? loaded[0]?.id ?? null);
    } catch (requestError) { setError(requestError.message || "Unable to load quotation comparisons"); }
    finally { setLoading(false); }
  }, []);
  useEffect(() => { fetchProjects(); }, [fetchProjects]);
  useEffect(() => {
    if (!["item", "item-prices", "supplier"].includes(panel)) return;
    const frame = window.requestAnimationFrame(() => {
      activeFormRef.current?.scrollIntoView?.({ behavior: "smooth", block: "center" });
    });
    return () => window.cancelAnimationFrame(frame);
  }, [panel, editingItem, editingQuote]);

  const project = projects.find((item) => item.id === selectedId) || null;
  const filtered = projects.filter((item) => `${item.title} ${item.category}`.toLowerCase().includes(query.toLowerCase()));
  const rankings = useMemo(() => project ? getCompleteQuoteRankings(project) : [], [project]);
  const lowestId = rankings[0]?.quote.id ?? null;

  async function mutate(request, message) {
    setSaving(true); setError("");
    try {
      const response = await request(); const updated = normalizeQuotationProjects([response.data.data])[0];
      setProjects((current) => current.map((item) => item.id === updated.id ? updated : item));
      setSelectedId(updated.id); setPanel(null); setEditingItem(null); setPricingItemId(null); setEditingQuote(null); toast.success(message);
      return updated;
    } catch (requestError) { setError(requestError.message || "That change could not be saved"); return null; }
    finally { setSaving(false); }
  }

  async function saveItem(form) {
    if (editingItem) {
      await mutate(
        () => api.patch(`/quotation-projects/${project.id}/items/${editingItem.id}`, form),
        "Item updated",
      );
      return;
    }

    const existingItemIds = new Set(project.items.map((item) => item.id));
    const updated = await mutate(
      () => api.post(`/quotation-projects/${project.id}/items`, form),
      "Item added",
    );
    const addedItem = updated?.items.find((item) => !existingItemIds.has(item.id));
    if (addedItem && updated.quotations.length) {
      setPricingItemId(addedItem.id);
      setPanel("item-prices");
    }
  }

  async function createProject(form) {
    setSaving(true); setError("");
    try {
      const response = await api.post("/quotation-projects", { ...form, currencyCode: "KES" });
      const created = normalizeQuotationProjects([response.data.data])[0];
      setProjects((current) => [created, ...current]); setSelectedId(created.id); setPanel(null); toast.success("Comparison created");
    } catch (requestError) { setError(requestError.message || "Unable to create comparison"); }
    finally { setSaving(false); }
  }

  async function deleteProject() {
    if (!project || !window.confirm(`Delete “${project.title}” and all its supplier quotations?`)) return;
    setSaving(true);
    try { await api.delete(`/quotation-projects/${project.id}`); const rest = projects.filter((item) => item.id !== project.id); setProjects(rest); setSelectedId(rest[0]?.id ?? null); setPanel(null); toast.success("Comparison deleted"); }
    catch (requestError) { setError(requestError.message || "Unable to delete comparison"); }
    finally { setSaving(false); }
  }

  return <div className="feature-page quotation-page">
    <header className="feature-page-header quotation-page-header"><div><h1>Quotation comparison</h1><p>List what you need, add each supplier’s prices, and compare the complete delivered cost side by side.</p></div><button type="button" className="feature-primary-button" onClick={() => setPanel("project-create")}><Plus size={17} /> New comparison</button></header>
    {error && <div className="quote-error" role="alert"><CircleAlert size={18} /><span>{error}</span><button type="button" onClick={() => setError("")} aria-label="Dismiss error"><X size={16} /></button></div>}
    {panel === "project-create" && <ProjectForm saving={saving} onCancel={() => setPanel(null)} onSubmit={createProject} />}
    <div className={`quote-workspace${projects.length > 1 ? "" : " quote-workspace-single"}`}>
      {projects.length > 1 && <aside className="quote-project-sidebar"><div className="quote-sidebar-heading"><div><small>Saved comparisons</small><strong>{projects.length}</strong></div><button className="quote-icon-button" type="button" onClick={() => setPanel("project-create")} aria-label="New comparison"><Plus size={17} /></button></div><label className="quote-search"><Search size={16} /><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Find a purchase" aria-label="Search comparisons" /></label><nav aria-label="Quotation comparisons">{filtered.map((item) => <button type="button" key={item.id} className={item.id === selectedId ? "is-active" : ""} onClick={() => { setSelectedId(item.id); setPanel(null); }}><span><strong>{item.title}</strong><small>{item.category}</small></span><small>{item.quotations.length} quotes</small></button>)}</nav></aside>}
      <main className="quote-main">
        {loading && <div className="quote-empty-state"><span className="loading-spinner" /><h2>Loading your comparisons…</h2></div>}
        {!loading && !project && <div className="quote-empty-state"><div className="quote-empty-symbol">Q</div><h2>Make the next supplier choice with evidence</h2><p>Create a comparison, add one shared item list, then record each supplier’s complete offer.</p><button className="feature-primary-button" type="button" onClick={() => setPanel("project-create")}><Plus size={17} /> Start a comparison</button></div>}
        {!loading && project && <>
          <section className="quote-project-overview"><div><span className="quote-status">{project.status === "supplier_selected" ? "Supplier chosen" : "Comparing"}</span><h2>{project.title}</h2><p>{project.notes || "No decision notes yet."}</p><div className="quote-project-meta"><span>{project.category}</span><span>{project.items.length} items</span><span>{project.quotations.length} suppliers</span></div></div><div className="quote-project-actions"><button className="quote-secondary-button" type="button" onClick={() => setPanel("project-edit")}><Pencil size={16} /> Edit</button><button className="quote-icon-button quote-danger-button" type="button" onClick={deleteProject} aria-label="Delete comparison"><Trash2 size={17} /></button></div></section>
          {panel === "project-edit" && <ProjectForm initial={project} saving={saving} onCancel={() => setPanel(null)} onSubmit={(form) => mutate(() => api.patch(`/quotation-projects/${project.id}`, { ...form, status: project.status }), "Comparison updated")} />}
          <section className="quote-section">
            <div className="quote-section-heading"><div><small>Step 1</small><h2>What you need</h2><p>List the items and quantities each supplier should price.</p></div><button className="quote-secondary-button" type="button" onClick={() => { setEditingItem(null); setPanel("item"); }}><Plus size={16} /> Add item</button></div>
            {panel === "item" && <div ref={activeFormRef}><ItemForm key={editingItem?.id || "new"} initialItem={editingItem} saving={saving} onCancel={() => { setPanel(null); setEditingItem(null); }} onSubmit={saveItem} /></div>}
            {!project.items.length ? <div className="quote-inline-empty"><strong>Start with one item.</strong><span>Adding an item unlocks supplier quotations.</span></div> : <div className="quote-request-list">{project.items.map((item) => <div key={item.id}><span><strong>{item.name}</strong><small>{item.quantity} {item.unit}</small></span><div className="quote-item-actions"><button type="button" className="quote-icon-button" aria-label={`Edit ${item.name}`} onClick={() => { setEditingItem(item); setPanel("item"); }}><Pencil size={15} /></button><button type="button" className="quote-icon-button quote-danger-button" aria-label={`Delete ${item.name}`} onClick={() => { if (window.confirm(`Remove ${item.name} from every quotation?`)) mutate(() => api.delete(`/quotation-projects/${project.id}/items/${item.id}`), "Item removed"); }}><Trash2 size={15} /></button></div></div>)}</div>}
            {panel === "item-prices" && pricingItemId && <div ref={activeFormRef}><ItemSupplierPriceForm key={pricingItemId} item={project.items.find((item) => item.id === pricingItemId)} quotations={project.quotations} saving={saving} onCancel={() => { setPanel(null); setPricingItemId(null); }} onSubmit={(payload) => mutate(() => api.patch(`/quotation-projects/${project.id}/items/${pricingItemId}/prices`, payload), "Supplier prices updated")} /></div>}
          </section>
          {!project.items.length ? <section className="quote-section quote-locked-step" aria-label="Supplier offers locked"><div className="quote-step-number">2</div><div><h2>Supplier quotations</h2><p>Add something you need above to unlock this step.</p></div></section> : <section className="quote-section"><div className="quote-section-heading"><div><small>Step 2</small><h2>Supplier quotations</h2><p>Enter each supplier’s prices. Delivery and tax details are optional.</p></div><button className="feature-primary-button" type="button" onClick={() => { setEditingQuote(null); setPanel("supplier"); }}><Plus size={16} /> Add supplier</button></div>{panel === "supplier" && <div ref={activeFormRef}><SupplierForm key={editingQuote?.id || "new"} items={project.items} initialQuote={editingQuote} saving={saving} onCancel={() => { setPanel(null); setEditingQuote(null); }} onSubmit={(payload) => mutate(() => editingQuote ? api.patch(`/quotation-projects/${project.id}/quotes/${editingQuote.id}`, payload) : api.post(`/quotation-projects/${project.id}/quotes`, payload), editingQuote ? "Quotation updated" : "Supplier quotation added")} /></div>}{!project.quotations.length ? <div className="quote-inline-empty"><strong>Add your first supplier.</strong><span>After that, add one more to unlock a side-by-side comparison.</span></div> : <div className="quote-offer-grid">{project.quotations.map((quote) => <QuoteCard key={quote.id} quote={quote} lowestId={lowestId} formatCurrency={formatCurrency} saving={saving} onEdit={(value) => { setEditingQuote(value); setPanel("supplier"); }} onDelete={(value) => { if (window.confirm(`Delete the quotation from ${value.supplier}?`)) mutate(() => api.delete(`/quotation-projects/${project.id}/quotes/${value.id}`), "Quotation deleted"); }} onPrefer={(value) => mutate(() => api.patch(`/quotation-projects/${project.id}/quotes/${value.id}/preference`, { preferred: !value.preferred }), value.preferred ? "Supplier choice removed" : `${value.supplier} selected`)} />)}</div>}</section>}
          {project.quotations.length < 2 ? <section className="quote-section quote-locked-step" aria-label="Comparison locked"><div className="quote-step-number">3</div><div><h2>Compare suppliers</h2><p>{project.items.length ? "Add quotations from two suppliers to unlock the comparison." : "Complete the first two steps to compare suppliers."}</p></div></section> : <section className="quote-section quote-comparison-section"><div className="quote-section-heading"><div><small>Step 3</small><h2>Compare suppliers</h2><p>Green cells show the lowest unit price. You still make the final choice.</p></div></div><DesktopComparison project={project} lowestId={lowestId} formatCurrency={formatCurrency} /><MobileComparison project={project} formatCurrency={formatCurrency} /></section>}
        </>}
      </main>
    </div>
  </div>;
}

export default Quotations;
