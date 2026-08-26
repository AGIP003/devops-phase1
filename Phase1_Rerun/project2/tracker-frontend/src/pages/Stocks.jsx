import {
  ArrowDownRight,
  ArrowUpRight,
  BarChart3,
  Bell,
  Bookmark,
  BookmarkCheck,
  Building2,
  Check,
  ChevronRight,
  CircleHelp,
  GitCompareArrows,
  Info,
  LineChart,
  RefreshCw,
  Search,
  ShieldCheck,
  SlidersHorizontal,
  X,
} from "lucide-react";
import { useCallback, useEffect, useMemo, useState } from "react";
import toast from "react-hot-toast";

import EChart from "../components/analytics/EChart";
import api from "../services/api";
import "./Stocks.css";

const WATCHLIST_STORAGE_KEY = "nse-watchlist-v1";
const LEGACY_WATCHLIST_STORAGE_KEY = "mock-nse-watchlist";
const ALERT_STORAGE_KEY = "nse-alerts-v1";
const DEFAULT_WATCHLIST = ["SCOM", "EQTY"];
const MAX_COMPARISONS = 3;

const TRADING_TERMS = [
  ["Last price", "The most recent price supplied by the source. It may be delayed or end-of-day, not a live executable quote."],
  ["Open price", "The price recorded when the current trading session opened."],
  ["Previous close", "The final recorded price from the previous trading session."],
  ["Day range", "The lowest and highest recorded prices during the trading session."],
  ["Volume", "The number of shares traded. Higher volume can mean easier trading, but volume alone says nothing about value."],
  ["Market capitalisation", "Share price multiplied by shares outstanding. It describes company size, not how much cash the company owns."],
  ["P/E ratio", "Price divided by earnings per share. It shows how much the market pays for one unit of earnings. Negative or missing earnings can make it unusable."],
  ["EPS", "Earnings per share: profit attributable to each ordinary share. Compare it over time and against similar companies."],
  ["Dividend yield", "Annual dividend per share divided by share price. A high yield can fall if dividends are cut."],
  ["DPS", "Dividend per share paid or declared for each ordinary share."],
  ["Return", "Percentage price movement over a stated period. Past returns do not predict future results."],
  ["Liquidity", "How easily shares can be bought or sold without moving the price significantly. Volume and bid–ask spread are common clues."],
  ["Bid–ask spread", "The gap between the highest buying price and lowest selling price. A wider spread usually means a higher trading cost."],
  ["P/B ratio", "Price compared with accounting book value per share. The current source does not supply it, so MoneyTiq does not estimate it."],
  ["ROE", "Return on equity: profit relative to shareholder equity. Useful within a sector, but the current source does not supply it."],
  ["Debt-to-equity", "Company debt relative to shareholder equity. It helps describe leverage, but the current source does not supply it."],
];

const METRIC_HELP = Object.fromEntries(TRADING_TERMS);

function readStoredList(key, fallback) {
  try {
    const storedValue = JSON.parse(localStorage.getItem(key));
    if (Array.isArray(storedValue)) return storedValue;
  } catch {
    // Invalid browser storage should never prevent the page from opening.
  }
  return fallback;
}

function initialWatchlist() {
  const current = readStoredList(WATCHLIST_STORAGE_KEY, null);
  return current || readStoredList(LEGACY_WATCHLIST_STORAGE_KEY, DEFAULT_WATCHLIST);
}

function numberValue(value) {
  if (value === null || value === undefined || value === "") return null;
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : null;
}

function formatPrice(value, currency = "KES") {
  const parsed = numberValue(value);
  if (parsed === null) return "Not supplied";
  return new Intl.NumberFormat("en-KE", {
    style: "currency",
    currency,
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(parsed);
}

function formatCompact(value, prefix = "") {
  const parsed = numberValue(value);
  if (parsed === null) return "Not supplied";
  return `${prefix}${new Intl.NumberFormat("en-KE", {
    notation: "compact",
    maximumFractionDigits: 2,
  }).format(parsed)}`;
}

function formatPercent(value) {
  const parsed = numberValue(value);
  if (parsed === null) return "Not supplied";
  return `${parsed > 0 ? "+" : ""}${parsed.toFixed(2)}%`;
}

function formatFreshness(value) {
  if (!value) return "Timestamp unavailable";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "Timestamp unavailable";
  return new Intl.DateTimeFormat("en-KE", {
    dateStyle: "medium",
    timeStyle: "short",
    timeZone: "Africa/Nairobi",
  }).format(date);
}

function movementClass(value) {
  const parsed = numberValue(value);
  if (parsed === null || parsed === 0) return "is-flat";
  return parsed > 0 ? "is-up" : "is-down";
}

function Movement({ value, compact = false }) {
  const parsed = numberValue(value);
  return (
    <span className={`nse-movement ${movementClass(value)} ${compact ? "is-compact" : ""}`.trim()}>
      {parsed !== null && parsed > 0 && <ArrowUpRight size={15} aria-hidden="true" />}
      {parsed !== null && parsed < 0 && <ArrowDownRight size={15} aria-hidden="true" />}
      {formatPercent(value)}
    </span>
  );
}

function MetricCard({ label, value, detail, tone = "" }) {
  return (
    <article className={`nse-metric ${tone}`.trim()}>
      <span>
        {label}
        {METRIC_HELP[label] && (
          <button type="button" title={METRIC_HELP[label]} aria-label={`What ${label} means`}>
            <Info size={13} aria-hidden="true" />
          </button>
        )}
      </span>
      <strong>{value}</strong>
      {detail && <small>{detail}</small>}
    </article>
  );
}

function Stocks() {
  const [market, setMarket] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState("");
  const [query, setQuery] = useState("");
  const [sector, setSector] = useState("All");
  const [sortBy, setSortBy] = useState("movement");
  const [followedTickers, setFollowedTickers] = useState(initialWatchlist);
  const [alertTickers, setAlertTickers] = useState(() =>
    readStoredList(ALERT_STORAGE_KEY, DEFAULT_WATCHLIST)
  );
  const [alertThreshold, setAlertThreshold] = useState(2);
  const [comparisonTickers, setComparisonTickers] = useState([]);
  const [detailCache, setDetailCache] = useState({});
  const [selectedTicker, setSelectedTicker] = useState(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [detailError, setDetailError] = useState("");

  const loadMarket = useCallback(async ({ manual = false } = {}) => {
    manual ? setRefreshing(true) : setLoading(true);
    setError("");
    try {
      const response = await api.get("/nse/stocks");
      setMarket(response.data);
    } catch (requestError) {
      setError(requestError.message || "NSE market data is temporarily unavailable.");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => { loadMarket(); }, [loadMarket]);
  useEffect(() => {
    localStorage.setItem(WATCHLIST_STORAGE_KEY, JSON.stringify(followedTickers));
  }, [followedTickers]);
  useEffect(() => {
    localStorage.setItem(ALERT_STORAGE_KEY, JSON.stringify(alertTickers));
  }, [alertTickers]);
  useEffect(() => {
    function closeOnEscape(event) {
      if (event.key === "Escape") setSelectedTicker(null);
    }
    window.addEventListener("keydown", closeOnEscape);
    return () => window.removeEventListener("keydown", closeOnEscape);
  }, []);

  const stocks = useMemo(() => market?.stocks || [], [market]);
  const sectors = useMemo(
    () => ["All", ...new Set(stocks.map((stock) => stock.sector).filter(Boolean))],
    [stocks]
  );
  const filteredStocks = useMemo(() => {
    const searchTerm = query.trim().toLowerCase();
    const matching = stocks.filter((stock) => {
      const matchesSector = sector === "All" || stock.sector === sector;
      const matchesSearch = !searchTerm || [stock.name, stock.ticker, stock.sector]
        .some((value) => String(value || "").toLowerCase().includes(searchTerm));
      return matchesSector && matchesSearch;
    });
    return [...matching].sort((left, right) => {
      if (sortBy === "name") return left.name.localeCompare(right.name);
      if (sortBy === "price") return (numberValue(right.price) || 0) - (numberValue(left.price) || 0);
      if (sortBy === "sector") return left.sector.localeCompare(right.sector) || left.name.localeCompare(right.name);
      return Math.abs(numberValue(right.changePercent) || 0) - Math.abs(numberValue(left.changePercent) || 0);
    });
  }, [query, sector, sortBy, stocks]);
  const followedStocks = useMemo(
    () => stocks.filter((stock) => followedTickers.includes(stock.ticker)),
    [followedTickers, stocks]
  );
  const advances = stocks.filter((stock) => (numberValue(stock.changePercent) || 0) > 0).length;
  const declines = stocks.filter((stock) => (numberValue(stock.changePercent) || 0) < 0).length;
  const triggeredAlerts = followedStocks.filter((stock) =>
    alertTickers.includes(stock.ticker)
    && Math.abs(numberValue(stock.changePercent) || 0) >= alertThreshold
  );
  const selectedDetail = selectedTicker ? detailCache[selectedTicker] : null;

  async function fetchDetail(stock, { open = false } = {}) {
    if (open) {
      setSelectedTicker(stock.ticker);
      setDetailError("");
    }
    if (detailCache[stock.ticker]) return detailCache[stock.ticker];
    if (open) setDetailLoading(true);
    try {
      const response = await api.get(`/nse/stocks/${encodeURIComponent(stock.symbol)}`);
      const detail = response.data.stock;
      setDetailCache((current) => ({ ...current, [stock.ticker]: detail }));
      return detail;
    } catch (requestError) {
      if (open) setDetailError(requestError.message || "Company details are unavailable.");
      return null;
    } finally {
      if (open) setDetailLoading(false);
    }
  }

  function toggleFollow(stock) {
    const followed = followedTickers.includes(stock.ticker);
    if (followed) {
      setFollowedTickers((current) => current.filter((ticker) => ticker !== stock.ticker));
      setAlertTickers((current) => current.filter((ticker) => ticker !== stock.ticker));
      toast.success(`${stock.ticker} removed from your watchlist`);
      return;
    }
    setFollowedTickers((current) => [...new Set([...current, stock.ticker])]);
    setAlertTickers((current) => [...new Set([...current, stock.ticker])]);
    toast.success(`${stock.ticker} saved to this device`);
  }

  function toggleAlert(stock) {
    const enabled = alertTickers.includes(stock.ticker);
    setAlertTickers((current) => enabled
      ? current.filter((ticker) => ticker !== stock.ticker)
      : [...new Set([...current, stock.ticker])]);
  }

  function toggleComparison(stock) {
    const selected = comparisonTickers.includes(stock.ticker);
    if (selected) {
      setComparisonTickers((current) => current.filter((ticker) => ticker !== stock.ticker));
      return;
    }
    if (comparisonTickers.length >= MAX_COMPARISONS) {
      toast.error("Compare up to three companies at a time");
      return;
    }
    setComparisonTickers((current) => [...current, stock.ticker]);
    fetchDetail(stock);
  }

  const chartOption = useMemo(() => {
    const history = selectedDetail?.priceHistory || [];
    return {
      animationDuration: 350,
      grid: { left: 12, right: 14, top: 20, bottom: 28, containLabel: true },
      tooltip: {
        trigger: "axis",
        valueFormatter: (value) => formatPrice(value, selectedDetail?.currency),
      },
      xAxis: {
        type: "category",
        boundaryGap: false,
        data: history.map((point) => point.date),
        axisLabel: { color: "#738076", hideOverlap: true },
        axisLine: { lineStyle: { color: "#dfe5df" } },
      },
      yAxis: {
        type: "value",
        scale: true,
        axisLabel: {
          color: "#738076",
          formatter: (value) => `${selectedDetail?.currency || "KES"} ${value}`,
        },
        splitLine: { lineStyle: { color: "#edf0ed" } },
      },
      series: [{
        type: "line",
        data: history.map((point) => numberValue(point.price)),
        smooth: 0.22,
        showSymbol: history.length < 16,
        symbolSize: 6,
        lineStyle: { color: "#64773b", width: 3 },
        itemStyle: { color: "#64773b" },
        areaStyle: { color: "rgba(100, 119, 59, 0.10)" },
      }],
    };
  }, [selectedDetail]);

  const comparisonStocks = comparisonTickers.map((ticker) => ({
    summary: stocks.find((stock) => stock.ticker === ticker),
    detail: detailCache[ticker],
  })).filter((entry) => entry.summary);

  if (loading) {
    return <div className="feature-page nse-page"><div className="nse-loading" role="status"><RefreshCw className="is-spinning" size={24} /><strong>Checking the NSE market feed…</strong><span>Validating prices, timestamps and company coverage.</span></div></div>;
  }
  if (error && !market) {
    return <div className="feature-page nse-page"><div className="nse-error" role="alert"><Building2 size={28} /><h1>Market data could not be loaded</h1><p>{error}</p><button type="button" onClick={() => loadMarket()}><RefreshCw size={16} /> Try again</button></div></div>;
  }

  return (
    <div className="feature-page nse-page">
      <header className="feature-page-header nse-page-header">
        <div><span className="nse-kicker">Nairobi Securities Exchange</span><h1>Market watch</h1><p>Explore price movement, compare companies and understand the terms behind the numbers.</p></div>
        <button type="button" className="nse-refresh-button" onClick={() => loadMarket({ manual: true })} disabled={refreshing}><RefreshCw className={refreshing ? "is-spinning" : ""} size={16} />{refreshing ? "Checking…" : "Refresh"}</button>
      </header>

      <section className={`nse-source-strip ${market.stale ? "is-stale" : ""}`} role="status">
        <ShieldCheck size={18} />
        <div><strong>{market.stale ? "Showing last validated market data" : "Licensed delayed market data"}</strong><span>Updated {formatFreshness(market.sourceUpdatedAt || market.fetchedAt)} EAT · Source <a href={market.source.url} target="_blank" rel="noreferrer">{market.source.name}</a> · {market.source.license}</span></div>
        <small>Information only · not an executable quote or investment advice</small>
      </section>

      <section className="nse-pulse-grid" aria-label="NSE market summary">
        <MetricCard label="Securities covered" value={stocks.length} detail="Validated listings in this feed" />
        <MetricCard label="Advancing" value={advances} detail="Positive supplied movement" tone="is-positive" />
        <MetricCard label="Declining" value={declines} detail="Negative supplied movement" tone="is-negative" />
        <MetricCard label="Sectors" value={Math.max(0, sectors.length - 1)} detail="Use filters for peer context" />
      </section>

      <div className="nse-workspace">
        <main className="nse-explorer">
          <div className="nse-section-header"><div><span className="nse-eyebrow">Company explorer</span><h2>Find a listed company</h2></div><span className="nse-result-count">{filteredStocks.length} results</span></div>
          <div className="nse-controls">
            <label className="nse-search"><Search size={17} /><span className="sr-only">Search listed companies</span><input type="search" value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search company, ticker or sector" />{query && <button type="button" onClick={() => setQuery("")} aria-label="Clear search"><X size={15} /></button>}</label>
            <label className="nse-select-control"><SlidersHorizontal size={16} /><span className="sr-only">Sort companies</span><select value={sortBy} onChange={(event) => setSortBy(event.target.value)}><option value="movement">Largest movement</option><option value="name">Company name</option><option value="price">Highest price</option><option value="sector">Sector</option></select></label>
          </div>
          <div className="nse-sector-tabs" aria-label="Filter companies by sector">
            {sectors.map((sectorName) => <button type="button" key={sectorName} className={sectorName === sector ? "active" : ""} onClick={() => setSector(sectorName)} aria-pressed={sectorName === sector}>{sectorName}</button>)}
          </div>
          <div className="nse-list-header" aria-hidden="true"><span>Company</span><span>Last price</span><span>Movement</span><span>Actions</span></div>
          <div className="nse-company-list">
            {filteredStocks.map((stock) => {
              const followed = followedTickers.includes(stock.ticker);
              const compared = comparisonTickers.includes(stock.ticker);
              return (
                <article className="nse-company-row" key={stock.symbol}>
                  <button type="button" className="nse-company-identity" onClick={() => fetchDetail(stock, { open: true })}><span className="nse-company-mark">{stock.ticker.slice(0, 2)}</span><span><strong>{stock.ticker}</strong><small>{stock.name}</small><em>{stock.sector}</em></span></button>
                  <div className="nse-row-price"><small>Last price</small><strong>{formatPrice(stock.price, stock.currency)}</strong></div>
                  <div className="nse-row-movement"><small>Movement</small><Movement value={stock.changePercent} /></div>
                  <div className="nse-row-actions">
                    <button type="button" className={compared ? "is-active" : ""} onClick={() => toggleComparison(stock)} aria-pressed={compared} aria-label={`${compared ? "Remove" : "Add"} ${stock.ticker} ${compared ? "from" : "to"} comparison`} title="Compare company">{compared ? <Check size={16} /> : <GitCompareArrows size={16} />}</button>
                    <button type="button" className={followed ? "is-active" : ""} onClick={() => toggleFollow(stock)} aria-pressed={followed} aria-label={`${followed ? "Remove" : "Save"} ${stock.ticker} ${followed ? "from" : "to"} watchlist`} title="Save company">{followed ? <BookmarkCheck size={16} /> : <Bookmark size={16} />}</button>
                    <button type="button" onClick={() => fetchDetail(stock, { open: true })} className="nse-view-button">View <ChevronRight size={15} /></button>
                  </div>
                </article>
              );
            })}
          </div>
          {!filteredStocks.length && <div className="nse-empty-state"><Search size={24} /><strong>No matching companies</strong><span>Try another ticker, company name or sector.</span><button type="button" onClick={() => { setQuery(""); setSector("All"); }}>Clear filters</button></div>}
        </main>

        <aside className="nse-sidebar">
          <section className="nse-side-card">
            <div className="nse-side-title"><div><BookmarkCheck size={18} /><span><small>Your watchlist</small><strong>{followedStocks.length} {followedStocks.length === 1 ? "company" : "companies"}</strong></span></div><label><span>Movement check</span><select value={alertThreshold} onChange={(event) => setAlertThreshold(Number(event.target.value))}>{[1, 2, 3, 5, 10].map((value) => <option value={value} key={value}>{value}%</option>)}</select></label></div>
            <p className="nse-local-note">Saved on this device. Cross-device alerts need the future notification service.</p>
            <div className="nse-watchlist">
              {followedStocks.map((stock) => {
                const enabled = alertTickers.includes(stock.ticker);
                return <div className="nse-watch-row" key={stock.ticker}><button type="button" onClick={() => fetchDetail(stock, { open: true })}><strong>{stock.ticker}</strong><span>{stock.name}</span></button><Movement value={stock.changePercent} compact /><button type="button" className={enabled ? "is-active" : ""} onClick={() => toggleAlert(stock)} aria-label={`${enabled ? "Disable" : "Enable"} on-screen movement check for ${stock.ticker}`} aria-pressed={enabled}><Bell size={15} /></button></div>;
              })}
              {!followedStocks.length && <p className="nse-empty-copy">Save companies from the explorer to keep them close.</p>}
            </div>
            {triggeredAlerts.length > 0 && <div className="nse-triggered"><strong>{triggeredAlerts.length} movement {triggeredAlerts.length === 1 ? "check" : "checks"}</strong><span>{triggeredAlerts.map((stock) => stock.ticker).join(", ")} crossed {alertThreshold}% in the supplied data.</span></div>}
          </section>

          <section className="nse-side-card nse-compare-card">
            <div className="nse-side-title"><div><GitCompareArrows size={18} /><span><small>Peer comparison</small><strong>{comparisonTickers.length} of {MAX_COMPARISONS} selected</strong></span></div></div>
            <p>Select companies from the same sector when possible; ratios mean more beside a genuine peer.</p>
            <div className="nse-compare-chips">{comparisonStocks.map(({ summary }) => <button type="button" key={summary.ticker} onClick={() => toggleComparison(summary)}>{summary.ticker}<X size={13} /></button>)}</div>
            {!comparisonTickers.length && <p className="nse-empty-copy">Use the compare icon beside a company to start.</p>}
          </section>

          <details className="nse-side-card nse-glossary">
            <summary><CircleHelp size={18} /><span><small>Plain-language guide</small><strong>Trading terms</strong></span><ChevronRight size={16} /></summary>
            <div>{TRADING_TERMS.map(([term, definition]) => <article key={term}><strong>{term}</strong><p>{definition}</p></article>)}</div>
          </details>
        </aside>
      </div>

      {comparisonStocks.length > 0 && (
        <section className="nse-comparison" aria-labelledby="nse-comparison-heading">
          <div className="nse-section-header"><div><span className="nse-eyebrow">Side-by-side evidence</span><h2 id="nse-comparison-heading">Company comparison</h2></div><button type="button" onClick={() => setComparisonTickers([])}>Clear comparison</button></div>
          <div className="nse-comparison-scroll"><table><thead><tr><th>Measure</th>{comparisonStocks.map(({ summary }) => <th key={summary.ticker}>{summary.ticker}<small>{summary.sector}</small></th>)}</tr></thead><tbody>
            {[
              ["Last price", ({ summary }) => formatPrice(summary.price, summary.currency)],
              ["Supplied movement", ({ summary }) => <Movement value={summary.changePercent} compact />],
              ["Market capitalisation", ({ detail }) => formatCompact(detail?.marketCap, `${detail?.currency || "KES"} `)],
              ["P/E ratio", ({ detail }) => detail?.peRatio ?? "Not supplied"],
              ["EPS", ({ detail }) => detail?.eps ? formatPrice(detail.eps, detail.currency) : "Not supplied"],
              ["Dividend yield", ({ detail }) => formatPercent(detail?.dividendYield)],
              ["DPS", ({ detail }) => detail?.dividendPerShare ? formatPrice(detail.dividendPerShare, detail.currency) : "Not supplied"],
              ["Volume", ({ detail }) => formatCompact(detail?.volume)],
              ["1-year return", ({ detail }) => formatPercent(detail?.performance?.["1Y"])],
              ["YTD return", ({ detail }) => formatPercent(detail?.performance?.YTD)],
            ].map(([label, render]) => <tr key={label}><th>{label}</th>{comparisonStocks.map((entry) => <td key={entry.summary.ticker}>{entry.detail ? render(entry) : <span className="nse-loading-value">Loading…</span>}</td>)}</tr>)}
          </tbody></table></div>
          <p className="nse-comparison-note"><Info size={14} /> Missing values are shown as “Not supplied.” MoneyTiq does not manufacture financial ratios.</p>
        </section>
      )}

      {selectedTicker && (
        <div className="nse-detail-overlay" role="presentation" onMouseDown={(event) => { if (event.target === event.currentTarget) setSelectedTicker(null); }}>
          <section className="nse-detail-panel" role="dialog" aria-modal="true" aria-labelledby="nse-detail-title">
            <button type="button" className="nse-detail-close" onClick={() => setSelectedTicker(null)} aria-label="Close company details"><X size={20} /></button>
            {detailLoading && <div className="nse-detail-loading" role="status"><RefreshCw className="is-spinning" /><strong>Loading company evidence…</strong></div>}
            {detailError && <div className="nse-detail-error" role="alert"><p>{detailError}</p><button type="button" onClick={() => { const stock = stocks.find((item) => item.ticker === selectedTicker); if (stock) fetchDetail(stock, { open: true }); }}>Try again</button></div>}
            {selectedDetail && !detailLoading && (
              <>
                <header className="nse-detail-header"><span className="nse-company-mark">{selectedDetail.ticker.slice(0, 2)}</span><div><span>{selectedDetail.ticker} · {selectedDetail.sector}</span><h2 id="nse-detail-title">{selectedDetail.name}</h2><p>{selectedDetail.industry || "Industry not supplied"}{selectedDetail.isin ? ` · ISIN ${selectedDetail.isin}` : ""}</p></div><div className="nse-detail-quote"><strong>{formatPrice(selectedDetail.price, selectedDetail.currency)}</strong><Movement value={selectedDetail.changePercent} /></div></header>
                <div className="nse-detail-status"><span>{selectedDetail.eodStatus || "Quote status not supplied"}</span><span>Confidence: {selectedDetail.quoteConfidence || "not supplied"}</span><span>As of {formatFreshness(selectedDetail.lastPriceUpdate || selectedDetail.priceAsOf)} EAT</span></div>
                {selectedDetail.description && <p className="nse-description">{selectedDetail.description}</p>}

                <section className="nse-detail-section"><div className="nse-detail-section-title"><LineChart size={17} /><div><h3>Price history</h3><p>Direction and scale over the dates supplied by the source.</p></div></div>{selectedDetail.priceHistory?.length > 1 ? <EChart option={chartOption} ariaLabel={`${selectedDetail.name} supplied price history`} className="nse-price-chart" /> : <div className="nse-chart-empty">Not enough verified history to draw a chart.</div>}</section>

                <section className="nse-detail-section"><div className="nse-detail-section-title"><BarChart3 size={17} /><div><h3>Trading snapshot</h3><p>Session activity and company size.</p></div></div><div className="nse-detail-metrics"><MetricCard label="Open price" value={formatPrice(selectedDetail.openPrice, selectedDetail.currency)} /><MetricCard label="Previous close" value={formatPrice(selectedDetail.previousClose, selectedDetail.currency)} /><MetricCard label="Day range" value={selectedDetail.dayLow || selectedDetail.dayHigh ? `${formatPrice(selectedDetail.dayLow, selectedDetail.currency)} – ${formatPrice(selectedDetail.dayHigh, selectedDetail.currency)}` : "Not supplied"} /><MetricCard label="Volume" value={formatCompact(selectedDetail.volume)} /><MetricCard label="Market capitalisation" value={formatCompact(selectedDetail.marketCap, `${selectedDetail.currency || "KES"} `)} /><MetricCard label="Shares outstanding" value={formatCompact(selectedDetail.sharesOutstanding)} /></div></section>

                <section className="nse-detail-section"><div className="nse-detail-section-title"><CircleHelp size={17} /><div><h3>Fundamentals and ratios</h3><p>Useful context, never a recommendation by itself.</p></div></div><div className="nse-detail-metrics"><MetricCard label="P/E ratio" value={selectedDetail.peRatio ?? "Not supplied"} /><MetricCard label="EPS" value={selectedDetail.eps ? formatPrice(selectedDetail.eps, selectedDetail.currency) : "Not supplied"} /><MetricCard label="Dividend yield" value={formatPercent(selectedDetail.dividendYield)} /><MetricCard label="DPS" value={selectedDetail.dividendPerShare ? formatPrice(selectedDetail.dividendPerShare, selectedDetail.currency) : "Not supplied"} /></div><p className="nse-unavailable-ratios">P/B, ROE, debt-to-equity, current ratio and free-cash-flow yield are not supplied by this source, so they are not estimated.</p></section>

                <section className="nse-detail-section"><div className="nse-detail-section-title"><BarChart3 size={17} /><div><h3>Price returns</h3><p>Historical price movement for each available period.</p></div></div><div className="nse-performance-grid">{Object.entries(selectedDetail.performance || {}).map(([period, value]) => <div key={period}><span>{period}</span><Movement value={value} compact /></div>)}</div></section>

                <footer className="nse-detail-footer"><p><Info size={15} /> Past performance is not a reliable indicator of future results. Check company filings and a licensed broker before acting.</p>{selectedDetail.website && <a href={selectedDetail.website} target="_blank" rel="noreferrer">Company website <ChevronRight size={14} /></a>}</footer>
              </>
            )}
          </section>
        </div>
      )}
    </div>
  );
}

export default Stocks;
