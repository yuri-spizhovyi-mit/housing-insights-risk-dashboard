import { useEffect, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  Area,
  ComposedChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
} from "recharts";
import {
  Building2,
  RefreshCw,
  Moon,
  Sun,
  Activity,
  MapPin,
  ArrowUpRight,
} from "lucide-react";
import {
  base,
  getForecast,
  getRisk,
  getCities,
  forecastKey,
  readFilters,
  type Filters,
  type Forecast,
  ApiError,
} from "./api";
import "./product.css";
const format = (v: number) =>
  new Intl.NumberFormat("en-CA", { maximumFractionDigits: 0 }).format(v);
function ForecastChart({ forecast }: { forecast: Forecast }) {
  const points = forecast.data.map((p) => ({
    ...p,
    band: p.lower !== null && p.upper !== null ? [p.lower, p.upper] : undefined,
  }));
  return (
    <>
      <div
        className="hi-chart"
        role="img"
        aria-label={`${forecast.city} experimental ${forecast.target} forecast. ${points.length} monthly observations. Values use the existing API scale; source units have not been verified.`}
      >
        <ResponsiveContainer width="100%" height={340}>
          <ComposedChart
            data={points}
            margin={{ top: 20, right: 20, left: 10, bottom: 10 }}
          >
            <CartesianGrid vertical={false} stroke="var(--hi-border)" />
            <XAxis
              dataKey="date"
              minTickGap={65}
              tickFormatter={(s) => s.slice(0, 7)}
            />
            <YAxis
              width={85}
              domain={["auto", "auto"]}
              tickFormatter={(v) => format(v)}
            />
            <Tooltip
              formatter={(v) =>
                Array.isArray(v)
                  ? v.map((n) => format(Number(n))).join(" – ")
                  : format(Number(v))
              }
            />
            <Area
              dataKey="band"
              name="Reported lower–upper bounds"
              stroke="none"
              fill="#0d9488"
              fillOpacity={0.15}
              isAnimationActive={false}
            />
            <Line
              dataKey="value"
              name="Experimental forecast"
              dot={points.length === 1}
              stroke="#0d9488"
              strokeWidth={2.5}
              isAnimationActive={false}
            />
          </ComposedChart>
        </ResponsiveContainer>
      </div>
      <details className="hi-data-table">
        <summary>View forecast values</summary>
        <div className="hi-table-scroll">
          <table>
            <caption>Forecast values · API scale (units unverified)</caption>
            <thead>
              <tr>
                <th>Date</th>
                <th>Forecast</th>
                <th>Lower bound</th>
                <th>Upper bound</th>
              </tr>
            </thead>
            <tbody>
              {points.map((p) => (
                <tr key={p.date}>
                  <td>{p.date}</td>
                  <td>{format(p.value)}</td>
                  <td>{p.lower === null ? "Unavailable" : format(p.lower)}</td>
                  <td>{p.upper === null ? "Unavailable" : format(p.upper)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </details>
    </>
  );
}
function errorText(error: Error | null) {
  if (error instanceof ApiError) return error.message;
  return "Market data could not be loaded or validated. Please retry.";
}
export default function Product() {
  const [filters, setFilters] = useState(() => readFilters(location.search));
  const [methodology, setMethodology] = useState(false);
  const [dark, setDark] = useState(
    () => localStorage.getItem("housing-theme") === "dark",
  );
  useEffect(() => {
    localStorage.setItem("housing-theme", dark ? "dark" : "light");
  }, [dark]);
  useEffect(() => {
    const pop = () => setFilters(readFilters(location.search));
    addEventListener("popstate", pop);
    return () => removeEventListener("popstate", pop);
  }, []);
  const change = (key: keyof Filters, value: string) => {
    const next = readFilters(
      new URLSearchParams({ ...filters, [key]: value }).toString(),
    );
    setFilters(next);
    history.pushState(null, "", "?" + new URLSearchParams(next));
  };
  const citiesQuery = useQuery({
    queryKey: ["cities-mvp"],
    queryFn: ({ signal }) => getCities(signal),
    retry: 1,
    staleTime: 300000,
  });
  const forecast = useQuery({
    queryKey: forecastKey(filters),
    queryFn: ({ signal }) => getForecast(filters, signal),
    retry: 1,
  });
  const risk = useQuery({
    queryKey: ["risk-mvp", filters.city],
    queryFn: ({ signal }) => getRisk(filters.city, signal),
    retry: 1,
  });
  const cities = Array.from(
    new Set([
      filters.city,
      ...(citiesQuery.data ?? ["Calgary", "Toronto", "Vancouver"]),
    ]),
  );
  const points = forecast.data?.data ?? [];
  const first = points[0];
  const last = points.at(-1);
  const expired = !!last && last.date < new Date().toLocaleDateString("en-CA");
  const refresh = () => {
    void forecast.refetch();
    void risk.refetch();
  };
  return (
    <div className={`hi ${dark ? "hi-dark" : ""}`}>
      <aside className="hi-side">
        <a className="hi-brand" href="?">
          <Building2 />
          <span>
            Housing<span>Insights</span>
          </span>
        </a>
        <div className="hi-nav-label">WORKSPACE</div>
        <button
          className={!methodology ? "active" : ""}
          onClick={() => setMethodology(false)}
        >
          Market overview
          <ArrowUpRight size={15} />
        </button>
        <button
          className={methodology ? "active" : ""}
          onClick={() => setMethodology(true)}
        >
          About the data
          <ArrowUpRight size={15} />
        </button>
        <div className="hi-side-note">
          <Activity size={20} />
          <b>Evidence before estimates.</b>
          <p>
            Explore Canadian housing projections with their limitations in view.
          </p>
        </div>
      </aside>
      <main className="hi-main">
        <header className="hi-top">
          <span>CANADIAN HOUSING MARKET INTELLIGENCE</span>
          <button
            aria-label={dark ? "Use light theme" : "Use dark theme"}
            onClick={() => setDark(!dark)}
          >
            {dark ? <Sun size={18} /> : <Moon size={18} />}
          </button>
        </header>
        <div className="hi-title">
          <div>
            <p className="hi-eyebrow">YOUR MARKET, IN CONTEXT</p>
            <h1>
              {methodology
                ? "Behind the numbers"
                : `${filters.city} housing outlook`}
            </h1>
            <p>Explore the outlook. Understand the limitations.</p>
          </div>
          <span className="hi-status">Experimental</span>
        </div>
        {methodology ? (
          <section className="hi-panel hi-method">
            <h2>Know what each number means.</h2>
            <h3>Experimental forecasts</h3>
            <p>
              This dashboard displays stored ARIMA, Prophet, and LSTM
              projections from the existing Housing Insights API. Changing
              filters retrieves stored results; it does not train a new model.
              Historical accuracy has not been validated here.
            </p>
            <h3>Values and dates</h3>
            <p>
              The API does not provide source definitions, verified units,
              training dates, or refresh timestamps. Values are therefore shown
              on the API scale, without assuming CAD or an index. Forecast dates
              are prediction periods, not data update dates. A date in the past
              means that stored projection is historical.
            </p>
            <h3>Uncertainty</h3>
            <p>
              Shading shows the API's lower and upper bounds when supplied. A
              probability level is not assumed. Missing bounds remain
              unavailable.
            </p>
            <h3>Risk indicators</h3>
            <p>
              Affordability, price-to-rent, and inventory classifications are
              displayed as reported by the API. Their methodology is unverified.
              The composite score is withheld.
            </p>
            <h3>Project and API</h3>
            <p>
              <a
                href="https://github.com/yuri-spizhovyi-mit/housing-insights-risk-dashboard"
                target="_blank"
                rel="noreferrer"
              >
                Project source and documentation
              </a>
            </p>
            <p>API: {base}</p>
          </section>
        ) : (
          <>
            <section className="hi-filters">
              <label>
                <MapPin size={16} /> Market
                <select
                  value={filters.city}
                  onChange={(e) => change("city", e.target.value)}
                >
                  {cities.map((c) => (
                    <option key={c}>{c}</option>
                  ))}
                </select>
              </label>
              <div className="hi-segment" aria-label="Forecast target">
                {["price", "rent"].map((t) => (
                  <button
                    aria-pressed={filters.target === t}
                    className={filters.target === t ? "selected" : ""}
                    key={t}
                    onClick={() => change("target", t)}
                  >
                    {t === "price" ? "Home prices" : "Rental market"}
                  </button>
                ))}
              </div>
              <button
                className="hi-refresh"
                disabled={forecast.isFetching || risk.isFetching}
                onClick={refresh}
              >
                <RefreshCw size={15} />
                {forecast.isFetching || risk.isFetching
                  ? "Updating…"
                  : "Refresh data"}
              </button>
            </section>
            {citiesQuery.isError && (
              <p className="hi-muted" role="status">
                City list unavailable. Showing default markets.
              </p>
            )}
            <div className="hi-notice" role="note">
              <b>Experimental forecast</b> · Source units, training dates, and
              historical accuracy are unverified.
              {expired &&
                " This stored forecast ends in the past; it is not a current outlook."}
            </div>
            <section className="hi-metrics hi-mvp-metrics">
              <article>
                <span>Forecast start</span>
                <strong>{first ? format(first.value) : "Unavailable"}</strong>
                <small>
                  {first
                    ? `${first.date} · API scale, units unverified`
                    : "No forecast loaded"}
                </small>
              </article>
              <article>
                <span>Forecast end</span>
                <strong>{last ? format(last.value) : "Unavailable"}</strong>
                <small>
                  {last
                    ? `${last.date} · API scale, units unverified`
                    : "No forecast loaded"}
                </small>
              </article>
              <article>
                <span>Projected change</span>
                <strong>
                  {first && last && first.value !== 0
                    ? `${((last.value / first.value - 1) * 100).toFixed(1)}%`
                    : "Unavailable"}
                </strong>
                <small>
                  First to last forecast point · not an observed annual change
                </small>
              </article>
            </section>
            <section className="hi-panel">
              <div className="hi-panel-heading">
                <div>
                  <p className="hi-eyebrow">MARKET TRAJECTORY</p>
                  <h2>
                    {filters.target === "price"
                      ? "Home price"
                      : "Rental market"}{" "}
                    projection
                  </h2>
                </div>
                <span className="hi-status">{filters.model.toUpperCase()}</span>
              </div>
              {forecast.isPending ? (
                <div className="hi-empty" role="status">
                  Loading forecast…
                </div>
              ) : forecast.isError ? (
                <div className="hi-empty" role="alert">
                  <Activity />
                  <h3>Forecast unavailable</h3>
                  <p>{errorText(forecast.error)}</p>
                  <button onClick={() => void forecast.refetch()}>
                    Retry forecast
                  </button>
                </div>
              ) : !points.length ? (
                <div className="hi-empty">
                  <h3>No forecast points</h3>
                  <p>Try another city or model.</p>
                </div>
              ) : (
                forecast.data && <ForecastChart forecast={forecast.data} />
              )}
              <div className="hi-chart-footer">
                <span>
                  Line: experimental forecast · Shading: reported bounds
                </span>
                <span>
                  {filters.horizon !== "1y"
                    ? "Long-range projection"
                    : "12-month selection"}{" "}
                  · API scale
                </span>
              </div>
            </section>
            <div className="hi-bottom">
              <section className="hi-panel">
                <p className="hi-eyebrow">REPORTED MARKET CONDITIONS</p>
                <h2>Risk indicators</h2>
                {risk.isPending ? (
                  <p role="status">Loading indicators…</p>
                ) : risk.isError ? (
                  <div role="alert">
                    <p>{errorText(risk.error)}</p>
                    <button onClick={() => void risk.refetch()}>
                      Retry indicators
                    </button>
                  </div>
                ) : (
                  risk.data && (
                    <>
                      <small>Indicator date: {risk.data.date}</small>
                      <dl className="hi-indicators">
                        {risk.data.breakdown.map((item, i) => (
                          <div key={`${item.name}-${i}`}>
                            <dt>{item.name}</dt>
                            <dd>{item.status}</dd>
                          </div>
                        ))}
                      </dl>
                    </>
                  )
                )}
                <p>
                  Classifications are reported by the API; methodology is
                  unverified. Composite score unavailable.
                </p>
              </section>
              <section className="hi-panel">
                <p className="hi-eyebrow">SOURCE NOTES</p>
                <h2>What is available</h2>
                <p>
                  These are stored model projections, not observed sale prices
                  or rents. Source definitions and the last refresh date are not
                  supplied by the API.
                </p>
                <p>
                  {first && last
                    ? `Forecast periods: ${first.date} to ${last.date}.`
                    : "Forecast periods: unavailable."}
                </p>
                <a
                  href="https://github.com/yuri-spizhovyi-mit/housing-insights-risk-dashboard"
                  target="_blank"
                  rel="noreferrer"
                >
                  View project documentation ↗
                </a>
              </section>
            </div>
            <details className="hi-panel hi-advanced">
              <summary>Forecast settings</summary>
              <label>
                Horizon
                <select
                  value={filters.horizon}
                  onChange={(e) => change("horizon", e.target.value)}
                >
                  <option value="1y">12 months</option>
                  <option value="2y">24 months · long-range</option>
                  <option value="5y">60 months · long-range</option>
                </select>
              </label>
              <label>
                Model
                <select
                  value={filters.model}
                  onChange={(e) => change("model", e.target.value)}
                >
                  {["arima", "prophet", "lstm"].map((m) => (
                    <option key={m} value={m}>
                      {m.toUpperCase()}
                    </option>
                  ))}
                </select>
              </label>
              <p>Availability varies by city, model, and horizon.</p>
            </details>
          </>
        )}
        <footer className="hi-footer">
          Housing Insights
          <span>
            Experimental research dashboard · Limitations stay visible.
          </span>
        </footer>
      </main>
    </div>
  );
}
