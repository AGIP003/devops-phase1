import { Plus, Printer } from "lucide-react";
import toast from "react-hot-toast";
import {
  getQuotationItemTotal,
  getQuotationTotal,
  quotationProjects,
} from "../data/mockFinanceFeatures";
import { useAdjustedCurrency } from "../hooks/useAdjustedCurrency";

const dateFormatter = new Intl.DateTimeFormat("en-KE", {
  day: "2-digit",
  month: "short",
  year: "numeric",
});

function QuotationProject({ project }) {
  const { formatCurrency } = useAdjustedCurrency();
  const totals = project.quotations.map((quote) => getQuotationTotal(project, quote));
  const bestTotal = Math.min(...totals);

  return (
    <section className="quote-project-card">
      <div className="quote-project-header">
        <div>
          <span className="coming-soon-pill">{project.category}</span>
          <h2>{project.title}</h2>
          <p>{project.quotations.length} quotations attached for the same item list</p>
        </div>
        <button
          type="button"
          className="feature-primary-button quote-pdf-button"
          onClick={() => toast.success("PDF generation preview")}
        >
          <Printer size={17} aria-hidden="true" />
          Generate PDF
        </button>
      </div>

      <div className="quote-table-wrap">
        <table className="quote-table">
          <thead>
            <tr>
              <th>Item</th>
              <th>Qty</th>
              {project.quotations.map((quote) => (
                <th key={quote.id}>
                  <span>{quote.supplier}</span>
                  <small>Valid {dateFormatter.format(new Date(quote.validUntil))}</small>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {project.items.map((item) => (
              <tr key={item.id}>
                <td>
                  <strong>{item.name}</strong>
                  <small>{item.unit}</small>
                </td>
                <td>{item.quantity}</td>
                {project.quotations.map((quote) => (
                  <td key={quote.id}>
                    <span>{formatCurrency(getQuotationItemTotal(item, quote))}</span>
                    <small>{formatCurrency(quote.items[item.id]?.unitPrice || 0)} each</small>
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
          <tfoot>
            <tr>
              <td>Total</td>
              <td />
              {project.quotations.map((quote) => {
                const total = getQuotationTotal(project, quote);
                return (
                  <td className={total === bestTotal ? "best-quote" : ""} key={quote.id}>
                    {formatCurrency(total)}
                    {total === bestTotal && <small>Best quote</small>}
                  </td>
                );
              })}
            </tr>
          </tfoot>
        </table>
      </div>
    </section>
  );
}

function Quotations() {
  return (
    <div className="feature-page">
      <div className="feature-page-header">
        <div>
          <span className="coming-soon-pill">Mock quotations</span>
          <h1>Quotations</h1>
          <p>Save supplier quotes, compare matching item lists, and print a clean comparison.</p>
        </div>
        <button type="button" className="feature-primary-button" disabled>
          <Plus size={17} aria-hidden="true" />
          Add quotation
        </button>
      </div>

      <section className="feature-summary-grid">
        <div className="feature-summary-card">
          <span>Quote Groups</span>
          <strong>{quotationProjects.length}</strong>
          <small>Grouped by project or purchase</small>
        </div>
        <div className="feature-summary-card">
          <span>Comparison Rule</span>
          <strong>Same items</strong>
          <small>Quantities match across suppliers</small>
        </div>
        <div className="feature-summary-card">
          <span>Next Step</span>
          <strong>Print & compare</strong>
          <small>PDF export is mocked for now</small>
        </div>
      </section>

      <div className="quote-project-list">
        {quotationProjects.map((project) => (
          <QuotationProject project={project} key={project.id} />
        ))}
      </div>
    </div>
  );
}

export default Quotations;
