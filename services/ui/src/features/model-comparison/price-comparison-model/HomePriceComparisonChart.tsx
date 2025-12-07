import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import { useState, useMemo } from "react";
import type { ForecastMetricsResponse } from "../../../types/model-comparison";

const MODEL_COLORS = {
  arima: "#60A5FA", // blue
  prophet: "#34D399", // green
  lstm: "#F472B6", // pink
};

const METRIC_OPTIONS = ["mae", "mape", "rmse"] as const;

const YEAR_TICKS = [0, 12, 24, 36, 48, 56];

function HomePriceComparisonChart({
  modelsData,
  selectedHorizonMonths = 60,
}: {
  modelsData: ForecastMetricsResponse | undefined;
  selectedHorizonMonths?: number;
}) {
  const [metric, setMetric] = useState<"mae" | "mape" | "rmse">("mae");

  const maxMonths = Math.min(selectedHorizonMonths, 56);

  const chartData = useMemo(() => {
    if (!modelsData) return [];

    const horizons = modelsData.horizons.filter((h) => h <= maxMonths);
    const { arima, prophet, lstm } = modelsData.models;

    return horizons.map((h, i) => ({
      horizon: h,
      arima: arima?.[i]?.[metric] ?? null,
      prophet: prophet?.[i]?.[metric] ?? null,
      lstm: lstm?.[i]?.[metric] ?? null,
    }));
  }, [modelsData, metric, maxMonths]);

  return (
    <div className="flex flex-col gap-4 w-full h-full">
      <div className="flex gap-2">
        {METRIC_OPTIONS.map((m) => (
          <button
            key={m}
            onClick={() => setMetric(m)}
            className={`px-3 py-1 rounded text-sm border transition ${
              metric === m
                ? "bg-blue-500 text-white border-blue-500"
                : "bg-gray-100 text-gray-700 border-gray-300"
            }`}
          >
            {m.toUpperCase()}
          </button>
        ))}
      </div>

      <ResponsiveContainer width="100%" height={350}>
        <LineChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />

          <XAxis
            dataKey="horizon"
            ticks={YEAR_TICKS.filter((t) => t <= maxMonths)}
            tickFormatter={(value) => {
              if (value === 0) return "0";
              if (value % 12 === 0) return `Y${value / 12}`;
              return "";
            }}
            interval={0}
            minTickGap={20}
            stroke="#6b7280"
          />

          <YAxis stroke="#6b7280" />

          <Tooltip
            formatter={(v) =>
              typeof v === "number" ? v.toLocaleString() : "–"
            }
            labelFormatter={(v) => `${v} months ahead`}
          />
          <Legend />

          <Line
            type="monotone"
            dataKey="arima"
            name="ARIMA"
            stroke={MODEL_COLORS.arima}
            strokeWidth={2}
            dot={false}
          />

          <Line
            type="monotone"
            dataKey="prophet"
            name="Prophet"
            stroke={MODEL_COLORS.prophet}
            strokeWidth={2}
            dot={false}
          />

          <Line
            type="monotone"
            dataKey="lstm"
            name="LSTM"
            stroke={MODEL_COLORS.lstm}
            strokeWidth={2}
            dot={false}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

export default HomePriceComparisonChart;
