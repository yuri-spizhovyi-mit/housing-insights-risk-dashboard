import {
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { MarketAnomaliesSeries } from "../../types/market-anomalies";
import { memo } from "react";

interface MarketAnomaliesChartProps {
  data: MarketAnomaliesSeries[] | undefined;
}

function transformData(data: MarketAnomaliesSeries[] | undefined) {
  // Time: O((m * s) + d log d), Space: O(map + sorted)
  if (!data) return [];

  const map = new Map<string, any>();

  for (const series of data) {
    const key = series.target;

    for (const point of series.signals) {
      if (!map.has(point.date)) {
        map.set(point.date, {
          date: point.date,
          [key]: point.score,
          isRentAnomaly: series.target === "rent" && point.is_anomaly,
          isHomeAnomaly: series.target === "price" && point.is_anomaly,
        });
      } else {
        const entry = map.get(point.date)!;
        entry[key] = point.score;
        entry.isRentAnomaly ||= series.target === "rent" && point.is_anomaly;
        entry.isHomeAnomaly ||= series.target === "price" && point.is_anomaly;
      }
    }
  }

  return [...map.values()].sort(
    (a, b) => new Date(a.date).getTime() - new Date(b.date).getTime()
  );
}

function MarketAnomaliesChart({ data }: MarketAnomaliesChartProps) {
  const transformedData = transformData(data);

  return (
    <ResponsiveContainer width="100%" height="100%">
      <LineChart data={transformedData}>
        <Line
          type="monotone"
          dataKey="rent"
          stroke="#fbbf24"
          strokeWidth={2}
          connectNulls={true}
          dot={{ r: 4 }}
          activeDot={{ r: 6 }}
        />

        <Line
          type="monotone"
          dataKey="price"
          stroke="#10b981"
          strokeWidth={2}
          connectNulls={true}
          dot={{ r: 4 }}
          activeDot={{ r: 6 }}
        />

        <XAxis
          dataKey="date"
          tickFormatter={(date) =>
            new Date(date).toLocaleDateString("en-US", {
              month: "short",
              year: "numeric",
            })
          }
          tick={{
            fontSize: 12,
            fill: "var(--text-primary)",
            opacity: 0.7,
            dy: 12,
          }}
          axisLine={{ stroke: "#333" }}
          tickLine
        />
        <YAxis
          tickFormatter={(val) => val.toFixed(1)}
          tick={{
            fontSize: 12,
            fill: "var(--text-primary)",
            opacity: 0.7,
            dy: -4,
          }}
          axisLine={{ stroke: "#333" }}
          tickLine
        />
        <Tooltip
          contentStyle={{
            background: "#111",
            border: "1px solid #333",
            fontSize: "14px",
          }}
          labelStyle={{ color: "#ffffff" }}
          formatter={(value: number, name: string, props: any) => [
            value.toFixed(2),
            name === "rent"
              ? props.payload.isRentAnomaly
                ? "Rent • Anomaly"
                : "Rent"
              : props.payload.isHomeAnomaly
              ? "Home • Anomaly"
              : "Home",
          ]}
          labelFormatter={(date) =>
            new Date(date).toLocaleDateString("en-US", {
              month: "short",
              year: "numeric",
            })
          }
        />
      </LineChart>
    </ResponsiveContainer>
  );
}

export default memo(MarketAnomaliesChart);
