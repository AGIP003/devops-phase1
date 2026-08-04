import {
  ArrowDownRight,
  ArrowUpRight,
  Bell,
  BellOff,
  Building2,
  Check,
  Eye,
  Lightbulb,
  Plus,
  Search,
  ShieldCheck,
  Sparkles,
} from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import toast from "react-hot-toast";
import { mockNseSectors, mockNseStocks } from "../data/mockNseStocks";
import "./Stocks.css";

const WATCHLIST_STORAGE_KEY = "mock-nse-watchlist";
const ALERT_STORAGE_KEY = "mock-nse-alerts";
const DEFAULT_WATCHLIST = ["SCOM", "EQTY"];

function readStoredList(key, fallback) {
  try {
    const storedValue = JSON.parse(localStorage.getItem(key));
    return Array.isArray(storedValue) ? storedValue : fallback;
  } catch {
    return fallback;
  }
}

function MiniTrend({ values, positive }) {
  const width = 150;
  const height = 42;
  const minimum = Math.min(...values);
  const maximum = Math.max(...values);
  const range = maximum - minimum || 1;
  const points = values
    .map((value, index) => {
      const x = (index / (values.length - 1)) * width;
      const y = height - ((value - minimum) / range) * (height - 8) - 4;
      return `${x},${y}`;
    })
    .join(" ");

  return (
    <svg
      className={`nse-mini-trend ${positive ? "is-up" : "is-down"}`}
      viewBox={`0 0 ${width} ${height}`}
      role="img"
      aria-label={`Illustrative ${positive ? "upward" : "downward"} price movement`}
    >
      <polyline points={points} />
    </svg>
  );
}

function Stocks() {
  const [query, setQuery] = useState("");
  const [sector, setSector] = useState("All");
  const [followedTickers, setFollowedTickers] = useState(() =>
    readStoredList(WATCHLIST_STORAGE_KEY, DEFAULT_WATCHLIST)
  );
  const [alertTickers, setAlertTickers] = useState(() =>
    readStoredList(ALERT_STORAGE_KEY, DEFAULT_WATCHLIST)
  );
  const [alertThreshold, setAlertThreshold] = useState(2);

  useEffect(() => {
    localStorage.setItem(WATCHLIST_STORAGE_KEY, JSON.stringify(followedTickers));
  }, [followedTickers]);

  useEffect(() => {
    localStorage.setItem(ALERT_STORAGE_KEY, JSON.stringify(alertTickers));
  }, [alertTickers]);

  const followedStocks = useMemo(
    () => mockNseStocks.filter((stock) => followedTickers.includes(stock.ticker)),
    [followedTickers]
  );

  const coveredSectors = useMemo(
    () => new Set(followedStocks.map((stock) => stock.sector)),
    [followedStocks]
  );

  const filteredStocks = useMemo(() => {
    const searchTerm = query.trim().toLowerCase();
    return mockNseStocks.filter((stock) => {
      const matchesSector = sector === "All" || stock.sector === sector;
      const matchesSearch =
        !searchTerm ||
        stock.name.toLowerCase().includes(searchTerm) ||
        stock.ticker.toLowerCase().includes(searchTerm) ||
        stock.sector.toLowerCase().includes(searchTerm);
      return matchesSector && matchesSearch;
    });
  }, [query, sector]);

  const discoveryStock = useMemo(() => {
    const unfollowedStocks = mockNseStocks.filter(
      (stock) => !followedTickers.includes(stock.ticker)
    );
    return (
      unfollowedStocks.find((stock) => !coveredSectors.has(stock.sector)) ||
      unfollowedStocks[0] ||
      null
    );
  }, [coveredSectors, followedTickers]);

  const peerComparisonStock = useMemo(() => {
    if (!followedStocks.length) return null;
    return (
      mockNseStocks.find(
        (stock) =>
          !followedTickers.includes(stock.ticker) &&
          coveredSectors.has(stock.sector)
      ) || null
    );
  }, [coveredSectors, followedStocks.length, followedTickers]);

  const triggeredAlerts = followedStocks.filter(
    (stock) =>
      alertTickers.includes(stock.ticker) &&
      Math.abs(stock.changePercent) >= alertThreshold
  );

  function toggleFollow(stock) {
    const isFollowed = followedTickers.includes(stock.ticker);
    if (isFollowed) {
      setFollowedTickers((current) =>
        current.filter((ticker) => ticker !== stock.ticker)
      );
      setAlertTickers((current) =>
        current.filter((ticker) => ticker !== stock.ticker)
      );
      toast.success(`${stock.ticker} removed from your mock watchlist`);
      return;
    }

    setFollowedTickers((current) => [...current, stock.ticker]);
    setAlertTickers((current) => [...new Set([...current, stock.ticker])]);
    toast.success(`${stock.ticker} added with demo alerts on`);
  }

  function toggleAlert(stock) {
    const alertsEnabled = alertTickers.includes(stock.ticker);
    setAlertTickers((current) =>
      alertsEnabled
        ? current.filter((ticker) => ticker !== stock.ticker)
        : [...current, stock.ticker]
    );
    toast.success(
      `${stock.ticker} demo alerts ${alertsEnabled ? "paused" : "enabled"}`
    );
  }

  return (
    <div className="feature-page nse-page">
      <div className="feature-page-header">
        <div>
          <span className="coming-soon-pill">Frontend market mock</span>
          <h1>NSE Market Watch</h1>
          <p>Build a focused company watchlist and decide which changes deserve your attention.</p>
        </div>
        <div className="nse-header-status" aria-label={`${followedStocks.length} companies followed`}>
          <Eye size={18} aria-hidden="true" />
          <span>
            <strong>{followedStocks.length}</strong>
            followed
          </span>
        </div>
      </div>

      <div className="nse-demo-notice" role="note">
        <ShieldCheck size={18} aria-hidden="true" />
        <p>
          <strong>Demo data only.</strong> Prices, movements, and insights are illustrative—not live NSE data or investment advice.
        </p>
      </div>

      <section className="feature-summary-grid" aria-label="Watchlist summary">
        <div className="feature-summary-card nse-summary-card">
          <span>Watchlist</span>
          <strong>{followedStocks.length}</strong>
          <small>Companies currently followed</small>
        </div>
        <div className="feature-summary-card nse-summary-card">
          <span>Sector coverage</span>
          <strong>{coveredSectors.size}</strong>
          <small>Different sectors represented</small>
        </div>
        <div className="feature-summary-card nse-summary-card">
          <span>Demo alerts</span>
          <strong>{triggeredAlerts.length}</strong>
          <small>Moves beyond your {alertThreshold}% threshold</small>
        </div>
      </section>

      <div className="nse-layout">
        <section className="nse-market-card">
          <div className="nse-section-heading">
            <div>
              <span className="nse-eyebrow">Company explorer</span>
              <h2>Choose companies to follow</h2>
            </div>
            <label className="nse-search">
              <Search size={17} aria-hidden="true" />
              <span className="sr-only">Search companies</span>
              <input
                type="search"
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                placeholder="Search name, ticker, or sector"
              />
            </label>
          </div>

          <div className="nse-sector-filters" aria-label="Filter companies by sector">
            {mockNseSectors.map((sectorName) => (
              <button
                type="button"
                className={sectorName === sector ? "active" : ""}
                key={sectorName}
                onClick={() => setSector(sectorName)}
                aria-pressed={sectorName === sector}
              >
                {sectorName}
              </button>
            ))}
          </div>

          <div className="nse-company-grid">
            {filteredStocks.map((stock) => {
              const isFollowed = followedTickers.includes(stock.ticker);
              const isPositive = stock.changePercent >= 0;
              return (
                <article className={`nse-stock-card ${isFollowed ? "is-followed" : ""}`} key={stock.ticker}>
                  <div className="nse-stock-heading">
                    <span className="nse-company-mark" aria-hidden="true">{stock.ticker.slice(0, 2)}</span>
                    <div>
                      <strong>{stock.ticker}</strong>
                      <small>{stock.name}</small>
                    </div>
                    <span className="nse-sector-label">{stock.sector}</span>
                  </div>

                  <div className="nse-price-row">
                    <div>
                      <small>Demo price</small>
                      <strong>KES {stock.price.toLocaleString("en-KE", { minimumFractionDigits: 2 })}</strong>
                    </div>
                    <span className={isPositive ? "nse-change-up" : "nse-change-down"}>
                      {isPositive ? <ArrowUpRight size={16} /> : <ArrowDownRight size={16} />}
                      {Math.abs(stock.changePercent).toFixed(1)}%
                    </span>
                  </div>

                  <MiniTrend values={stock.history} positive={isPositive} />

                  <p className="nse-stock-insight">
                    <Lightbulb size={15} aria-hidden="true" />
                    <span>{stock.discoveryNote}</span>
                  </p>

                  <button
                    type="button"
                    className={`nse-follow-button ${isFollowed ? "is-followed" : ""}`}
                    onClick={() => toggleFollow(stock)}
                    aria-pressed={isFollowed}
                  >
                    {isFollowed ? <Check size={16} /> : <Plus size={16} />}
                    {isFollowed ? "Following" : "Follow company"}
                  </button>
                </article>
              );
            })}
          </div>

          {!filteredStocks.length && (
            <div className="nse-no-results">
              <Building2 size={24} aria-hidden="true" />
              <strong>No companies match those filters</strong>
              <button type="button" onClick={() => { setQuery(""); setSector("All"); }}>
                Clear filters
              </button>
            </div>
          )}
        </section>

        <aside className="nse-side-stack">
          <section className="nse-watchlist-card">
            <div className="nse-card-title">
              <div>
                <span className="nse-card-icon"><Bell size={18} /></span>
                <div>
                  <span className="nse-eyebrow">Your watchlist</span>
                  <h2>Alert controls</h2>
                </div>
              </div>
              <label className="nse-threshold-select">
                <span>Movement</span>
                <select
                  value={alertThreshold}
                  onChange={(event) => setAlertThreshold(Number(event.target.value))}
                >
                  <option value={1}>1%</option>
                  <option value={2}>2%</option>
                  <option value={3}>3%</option>
                  <option value={5}>5%</option>
                </select>
              </label>
            </div>

            <div className="nse-watchlist">
              {followedStocks.map((stock) => {
                const alertsEnabled = alertTickers.includes(stock.ticker);
                return (
                  <div className="nse-watchlist-row" key={stock.ticker}>
                    <span className="nse-watchlist-ticker">{stock.ticker}</span>
                    <div>
                      <strong>{stock.name}</strong>
                      <small>Alert when movement reaches {alertThreshold}%</small>
                    </div>
                    <button
                      type="button"
                      className={alertsEnabled ? "is-enabled" : ""}
                      onClick={() => toggleAlert(stock)}
                      aria-label={`${alertsEnabled ? "Pause" : "Enable"} ${stock.ticker} alerts`}
                      aria-pressed={alertsEnabled}
                    >
                      {alertsEnabled ? <Bell size={16} /> : <BellOff size={16} />}
                    </button>
                  </div>
                );
              })}

              {!followedStocks.length && (
                <div className="nse-empty-watchlist">
                  <Eye size={20} aria-hidden="true" />
                  <p>Follow a company to add it here and switch on demo alerts.</p>
                </div>
              )}
            </div>

            <div className="nse-delivery-note">
              <span>In-app preview</span>
              <small>Push, email, and Telegram delivery need the future backend.</small>
            </div>
          </section>

          <section className="nse-discovery-card">
            <div className="nse-card-title">
              <div>
                <span className="nse-card-icon is-spark"><Sparkles size={18} /></span>
                <div>
                  <span className="nse-eyebrow">Transparent nudges</span>
                  <h2>Discovery cues</h2>
                </div>
              </div>
            </div>
            <p className="nse-discovery-intro">
              These prompts explain why a company is surfaced. They do not rank expected returns.
            </p>

            {discoveryStock && (
              <article className="nse-nudge-card">
                <span>Explore a missing sector</span>
                <strong>{discoveryStock.ticker} · {discoveryStock.name}</strong>
                <p>{discoveryStock.discoveryNote}</p>
                <button type="button" onClick={() => toggleFollow(discoveryStock)}>
                  <Plus size={15} /> Follow {discoveryStock.ticker}
                </button>
              </article>
            )}

            {peerComparisonStock && (
              <article className="nse-nudge-card is-peer">
                <span>Compare a sector peer</span>
                <strong>{peerComparisonStock.ticker} · {peerComparisonStock.name}</strong>
                <p>{peerComparisonStock.discoveryNote}</p>
                <button type="button" onClick={() => toggleFollow(peerComparisonStock)}>
                  <Plus size={15} /> Follow {peerComparisonStock.ticker}
                </button>
              </article>
            )}
          </section>

          <section className="nse-alert-feed-card">
            <span className="nse-eyebrow">Demo notification feed</span>
            <h2>What would alert you</h2>
            {triggeredAlerts.length ? (
              <div className="nse-alert-feed">
                {triggeredAlerts.map((stock) => (
                  <div key={stock.ticker}>
                    <Bell size={15} aria-hidden="true" />
                    <p>
                      <strong>{stock.ticker} moved {Math.abs(stock.changePercent).toFixed(1)}%</strong>
                      <small>Illustrative movement crossed your {alertThreshold}% threshold.</small>
                    </p>
                  </div>
                ))}
              </div>
            ) : (
              <p className="nse-no-alerts">No followed company crosses the selected demo threshold.</p>
            )}
          </section>
        </aside>
      </div>
    </div>
  );
}

export default Stocks;
