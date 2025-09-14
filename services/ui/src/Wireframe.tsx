import React, { useMemo, useState, useEffect } from "react";
import {
  Download,
  MapPin,
  LineChart as LineChartIcon,
  Newspaper,
  AlertCircle,
  Home,
  DollarSign,
} from "lucide-react";
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  RadialBarChart,
  RadialBar,
  PolarAngleAxis,
} from "recharts";

export default function HousingDashboardWireframe() {
  const [city, setCity] = useState("Kelowna");
  const [horizon, setHorizon] = useState("5Y"); // 1Y | 2Y | 5Y | 10Y
  const [propertyType, setPropertyType] = useState("Condo");
  const [beds, setBeds] = useState("any"); // any | 1 | 2 | 3+
  const [baths, setBaths] = useState("any"); // any | 1 | 2 | 3+
  const [sqftMin, setSqftMin] = useState(500);
  const [sqftMax, setSqftMax] = useState(2500);
  const [yearBuilt, setYearBuilt] = useState("any"); // any | 2000+ | 2010+ | 2020+

  // ---------------------------------------------------------------------------
  // Utilities
  // ---------------------------------------------------------------------------
  const today = useMemo(() => {
    const d = new Date();
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}`; // YYYY-MM
  }, []);

  function addMonths(ym: string, k: number) {
    const [y, m] = ym.split("-").map(Number);
    const idx = y * 12 + (m - 1) + k; // month index
    const yy = Math.floor(idx / 12);
    const mm = (idx % 12) + 1;
    return `${yy}-${String(mm).padStart(2, "0")}`;
  }

  function monthsForward(startYM: string, count: number) {
    return Array.from({ length: count }).map((_, i) => addMonths(startYM, i));
  }

  // Projection generator (toy growth just for wireframe)
  function projectSeries(
    startValue: number,
    months: string[],
    jitterEvery = 6,
    slope = 5
  ) {
    return months.map((date, i) => ({
      date,
      value: startValue + i * slope + (i % jitterEvery === 0 ? 12 : 0),
    }));
  }

  // Horizon rules
  function getWindowAndStep(h: string) {
    switch (h) {
      case "1Y":
        return { window: 12, step: 1 } as const;
      case "2Y":
        return { window: 24, step: 2 } as const;
      case "5Y":
        return { window: 60, step: 6 } as const;
      case "10Y":
      default:
        return { window: 120, step: 12 } as const;
    }
  }

  // --- Lightweight runtime tests (won't affect UI) ---------------------------
  useEffect(() => {
    // getWindowAndStep tests
    console.assert(
      getWindowAndStep("1Y").window === 12 && getWindowAndStep("1Y").step === 1,
      "1Y mapping failed"
    );
    console.assert(
      getWindowAndStep("2Y").window === 24 && getWindowAndStep("2Y").step === 2,
      "2Y mapping failed"
    );
    console.assert(
      getWindowAndStep("5Y").window === 60 && getWindowAndStep("5Y").step === 6,
      "5Y mapping failed"
    );
    console.assert(
      getWindowAndStep("10Y").window === 120 &&
        getWindowAndStep("10Y").step === 12,
      "10Y mapping failed"
    );

    // monthsForward length test
    console.assert(
      monthsForward("2025-01", 3).length === 3,
      "monthsForward length failed"
    );
  }, []);

  // Build forward-looking series from *today*
  const { window: win, step } = getWindowAndStep(horizon);

  const priceSeries = useMemo(() => {
    const months = monthsForward(today, win);
    return projectSeries(750, months, 6, 6).filter(
      (_, idx) => idx % step === 0
    );
  }, [today, horizon]);

  const rentSeries = useMemo(() => {
    const months = monthsForward(today, win);
    return projectSeries(2300, months, 4, 5).filter(
      (_, idx) => idx % step === 0
    );
  }, [today, horizon]);

  // X ticks match sampled points
  const xTicks = useMemo(() => priceSeries.map((d) => d.date), [priceSeries]);

  const riskScore = 62; // 0..100 (placeholder)
  const riskData = [{ name: "risk", value: riskScore, fill: "#ef4444" }];

  const cities = ["Kelowna", "Vancouver", "Toronto"];
  const horizons = ["1Y", "2Y", "5Y", "10Y"];
  const propertyTypes = ["Condo", "House", "Town House", "Apartment"];

  // Pretty tick formatter
  const formatTick = (tick?: string) => {
    if (!tick) return tick as unknown as string;
    const [y, m] = tick.split("-");
    if (horizon === "10Y") return y; // yearly labels
    return `${y}-${m}`; // otherwise keep YYYY-MM for clarity
  };

  return (
    <div className="min-h-screen w-full bg-neutral-950 text-neutral-100">
      {/* Header */}
      <header className="flex items-center justify-between px-6 py-4 border-b border-neutral-800 bg-neutral-900/60 sticky top-0 backdrop-blur">
        <div className="flex items-center gap-3">
          <LineChartIcon className="size-6 text-neutral-300" />
          <h1 className="text-xl font-semibold tracking-tight">
            Housing Insights & Risk Forecast —{" "}
            <span className="opacity-80">Wireframe</span>
          </h1>
        </div>
        <div className="flex items-center gap-3">
          <button className="inline-flex items-center gap-2 rounded-2xl border border-neutral-700 px-4 py-2 hover:bg-neutral-800">
            <Download className="size-4" />
            Download PDF (stub)
          </button>
        </div>
      </header>

      {/* Controls Bar */}
      <section className="px-6 pt-6">
        <div className="grid grid-cols-12 gap-4">
          <div className="col-span-12 lg:col-span-12 flex flex-wrap items-center gap-3">
            {/* City Selector */}
            <div className="flex items-center gap-2 rounded-2xl border border-neutral-700 px-3 py-2">
              <MapPin className="size-4 opacity-70" />
              <span className="text-sm opacity-70">City</span>
              <select
                value={city}
                onChange={(e) => setCity(e.target.value)}
                className="bg-transparent focus:outline-none px-1"
              >
                {cities.map((c) => (
                  <option key={c} value={c} className="bg-neutral-900">
                    {c}
                  </option>
                ))}
              </select>
            </div>

            {/* Horizon Selector */}
            <div className="flex items-center gap-2 rounded-2xl border border-neutral-700 px-3 py-2">
              <span className="text-sm opacity-70">Horizon</span>
              <div className="flex rounded-xl overflow-hidden border border-neutral-700">
                {horizons.map((h) => (
                  <button
                    key={h}
                    onClick={() => setHorizon(h)}
                    className={`px-3 py-1.5 text-sm ${
                      horizon === h
                        ? "bg-neutral-200 text-neutral-900"
                        : "bg-neutral-900 hover:bg-neutral-800"
                    }`}
                  >
                    {h}
                  </button>
                ))}
              </div>
            </div>

            {/* Property Type */}
            <div className="flex items-center gap-2 rounded-2xl border border-neutral-700 px-3 py-2">
              <span className="text-sm opacity-70">Type</span>
              <select
                value={propertyType}
                onChange={(e) => setPropertyType(e.target.value)}
                className="bg-transparent focus:outline-none px-1"
              >
                {propertyTypes.map((t) => (
                  <option key={t} value={t} className="bg-neutral-900">
                    {t}
                  </option>
                ))}
              </select>
            </div>

            {/* Beds */}
            <div className="flex items-center gap-2 rounded-2xl border border-neutral-700 px-3 py-2 text-sm">
              <label className="opacity-70">Beds</label>
              <select
                value={beds}
                onChange={(e) => setBeds(e.target.value)}
                className="bg-transparent focus:outline-none"
              >
                <option value="any" className="bg-neutral-900">
                  Any
                </option>
                <option value="1" className="bg-neutral-900">
                  1
                </option>
                <option value="2" className="bg-neutral-900">
                  2
                </option>
                <option value="3+" className="bg-neutral-900">
                  3+
                </option>
              </select>
            </div>

            {/* Baths */}
            <div className="flex items-center gap-2 rounded-2xl border border-neutral-700 px-3 py-2 text-sm">
              <label className="opacity-70">Baths</label>
              <select
                value={baths}
                onChange={(e) => setBaths(e.target.value)}
                className="bg-transparent focus:outline-none"
              >
                <option value="any" className="bg-neutral-900">
                  Any
                </option>
                <option value="1" className="bg-neutral-900">
                  1
                </option>
                <option value="2" className="bg-neutral-900">
                  2
                </option>
                <option value="3+" className="bg-neutral-900">
                  3+
                </option>
              </select>
            </div>

            {/* Sqft Range */}
            <div className="flex items-center gap-2 rounded-2xl border border-neutral-700 px-3 py-2 text-sm">
              <label className="opacity-70">Sqft</label>
              <div className="flex items-center gap-2">
                <input
                  type="range"
                  min={300}
                  max={5000}
                  step={50}
                  value={sqftMin}
                  onChange={(e) =>
                    setSqftMin(Math.min(Number(e.target.value), sqftMax - 50))
                  }
                />
                <span className="opacity-70 text-xs">min {sqftMin}</span>
                <input
                  type="range"
                  min={350}
                  max={5500}
                  step={50}
                  value={sqftMax}
                  onChange={(e) =>
                    setSqftMax(Math.max(Number(e.target.value), sqftMin + 50))
                  }
                />
                <span className="opacity-70 text-xs">max {sqftMax}</span>
              </div>
            </div>

            {/* Year Built (optional) */}
            <div className="flex items-center gap-2 rounded-2xl border border-neutral-700 px-3 py-2 text-sm">
              <label className="opacity-70">Year built</label>
              <select
                value={yearBuilt}
                onChange={(e) => setYearBuilt(e.target.value)}
                className="bg-transparent focus:outline-none"
              >
                <option value="any" className="bg-neutral-900">
                  Any
                </option>
                <option value="2000+" className="bg-neutral-900">
                  2000+
                </option>
                <option value="2010+" className="bg-neutral-900">
                  2010+
                </option>
                <option value="2020+" className="bg-neutral-900">
                  2020+
                </option>
              </select>
            </div>

            {/* Predict Button */}
            <button
              className="ml-4 px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-sm font-semibold"
              onClick={() =>
                console.log("Predict clicked with:", {
                  city,
                  horizon,
                  propertyType,
                  beds,
                  baths,
                  sqftMin,
                  sqftMax,
                  yearBuilt,
                })
              }
            >
              Predict
            </button>
          </div>
        </div>
      </section>

      {/* Main Grid */}
      <main className="px-6 py-6 grid grid-cols-12 gap-4">
        {/* Price Forecast */}
        <div className="col-span-12 lg:col-span-8 rounded-2xl border border-neutral-800 bg-neutral-900 p-4">
          <div className="flex items-center justify-between mb-3">
            <h2 className="font-semibold flex items-center gap-2">
              <Home className="size-5 opacity-80" /> Home Price Forecast
            </h2>
            <span className="text-xs opacity-60">
              prophet-like · 80/95% bands (stub)
            </span>
          </div>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={priceSeries}>
                <XAxis
                  dataKey="date"
                  ticks={xTicks}
                  tickFormatter={formatTick}
                  tick={{ fontSize: 12, fill: "#a3a3a3" }}
                />
                <YAxis tick={{ fontSize: 12, fill: "#a3a3a3" }} />
                <Tooltip
                  contentStyle={{
                    background: "#111",
                    border: "1px solid #333",
                  }}
                />
                <Line
                  type="monotone"
                  dataKey="value"
                  stroke="#60a5fa"
                  strokeWidth={2}
                  dot={false}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Risk Gauge + Indicators */}
        <aside className="col-span-12 lg:col-span-4 rounded-2xl border border-neutral-800 bg-neutral-900 p-4">
          <div className="flex items-center justify-between mb-3">
            <h2 className="font-semibold">Risk Gauge (macro + local)</h2>
            <span className="text-xs opacity-60">composite index (stub)</span>
          </div>
          <div className="flex gap-4 items-center">
            <div className="h-40 w-40">
              <ResponsiveContainer width="100%" height="100%">
                <RadialBarChart
                  innerRadius="60%"
                  outerRadius="100%"
                  data={riskData}
                  startAngle={180}
                  endAngle={0}
                >
                  <PolarAngleAxis
                    type="number"
                    domain={[0, 100]}
                    tick={false}
                  />
                  <RadialBar dataKey="value" cornerRadius={20} />
                </RadialBarChart>
              </ResponsiveContainer>
            </div>
            <div className="flex-1 text-sm">
              <div className="flex items-center justify-between py-1 border-b border-neutral-800">
                <span className="opacity-80">Affordability</span>
                <span className="rounded-full px-2 py-0.5 text-xs bg-neutral-800">
                  Tight
                </span>
              </div>
              <div className="flex items-center justify-between py-1 border-b border-neutral-800">
                <span className="opacity-80">Price-to-Rent</span>
                <span className="rounded-full px-2 py-0.5 text-xs bg-neutral-800">
                  Elevated
                </span>
              </div>
              <div className="flex items-center justify-between py-1">
                <span className="opacity-80">Inventory</span>
                <span className="rounded-full px-2 py-0.5 text-xs bg-neutral-800">
                  Low
                </span>
              </div>
            </div>
          </div>
          <div className="mt-3 text-xs flex items-start gap-2 opacity-70">
            <AlertCircle className="size-4" />
            <p>
              Interpretation: 0=low risk, 100=high risk. Composite for
              illustration.
            </p>
          </div>
        </aside>

        {/* Rent Forecast */}
        <div className="col-span-12 lg:col-span-8 rounded-2xl border border-neutral-800 bg-neutral-900 p-4">
          <div className="flex items-center justify-between mb-3">
            <h2 className="font-semibold flex items-center gap-2">
              <DollarSign className="size-5 opacity-80" /> Rent Forecast
            </h2>
            <span className="text-xs opacity-60">baseline (stub)</span>
          </div>
          <div className="h-60">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={rentSeries}>
                <XAxis
                  dataKey="date"
                  ticks={xTicks}
                  tickFormatter={formatTick}
                  tick={{ fontSize: 12, fill: "#a3a3a3" }}
                />
                <YAxis tick={{ fontSize: 12, fill: "#a3a3a3" }} />
                <Tooltip
                  contentStyle={{
                    background: "#111",
                    border: "1px solid #333",
                  }}
                />
                <Line
                  type="monotone"
                  dataKey="value"
                  stroke="#34d399"
                  strokeWidth={2}
                  dot={false}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Sentiment / News */}
        <section className="col-span-12 lg:col-span-4 rounded-2xl border border-neutral-800 bg-neutral-900 p-4">
          <div className="flex items-center gap-2 mb-3">
            <Newspaper className="size-4 opacity-80" />
            <h2 className="font-semibold">Sentiment & News</h2>
          </div>
          <ul className="space-y-3">
            {[
              {
                title: "Kelowna rental demand rises",
                tone: "pos",
                date: "2025-07-28",
              },
              {
                title: "Rate cuts delayed; affordability worsens",
                tone: "neg",
                date: "2025-08-14",
              },
              {
                title: "New supply targets announced",
                tone: "neu",
                date: "2025-08-29",
              },
            ].map((n, i) => (
              <li
                key={i}
                className="rounded-xl border border-neutral-800 p-3 bg-neutral-950"
              >
                <div className="text-sm font-medium line-clamp-1">
                  {n.title}
                </div>
                <div className="text-xs opacity-60 mt-1 flex items-center gap-2">
                  <span
                    className={`rounded-full px-2 py-0.5 border ${
                      n.tone === "pos"
                        ? "border-emerald-400 text-emerald-300"
                        : n.tone === "neg"
                        ? "border-rose-400 text-rose-300"
                        : "border-neutral-600 text-neutral-300"
                    }`}
                  >
                    {n.tone.toUpperCase()}
                  </span>
                  <span>{n.date}</span>
                </div>
              </li>
            ))}
          </ul>
        </section>

        {/* Footer / Notes */}
        <div className="col-span-12 rounded-2xl border border-neutral-800 bg-neutral-900 p-4">
          <h3 className="font-semibold mb-2">Wireframe Notes</h3>
          <ul className="list-disc pl-5 text-sm space-y-1 opacity-80">
            <li>
              Filters map to DB: bedrooms, bathrooms, area_sqft, year_built;
              property type maps to one-hot columns.
            </li>
            <li>
              Interpret UI values server-side: beds {">= 3"} when "3+", baths
              similarly; sqft uses [min, max].
            </li>
            <li>
              Horizon anchors at *today* and projects forward: 1Y (monthly), 2Y
              (every 2nd month), 5Y (every 6th month), 10Y (yearly).
            </li>
            <li>
              Charts show placeholder series; replace with real JSON from Spring
              → FastAPI.
            </li>
            <li>
              PDF button is non-functional; FE to call backend report endpoint
              or client PDF.
            </li>
            <li>
              Keep layout responsive (12-col grid). Mobile: stack cards
              vertically.
            </li>
          </ul>
        </div>
      </main>
    </div>
  );
}
