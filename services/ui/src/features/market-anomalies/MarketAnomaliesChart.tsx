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

function shouldRenderDot(index: number, isAnomaly: boolean) {
  if (isAnomaly) return true;
  const showEvery = 3;
  return index % showEvery === 0;
}

const AnomalyDot = (props: any) => {
  const { cx, cy, payload, index, dataKey, stroke } = props;

  const isAnomaly = dataKey === "price" && payload.isHomeAnomaly;

  if (!shouldRenderDot(index, isAnomaly)) return null;

  return (
    <circle
      cx={cx}
      cy={cy}
      r={isAnomaly ? 6 : 4}
      fill={isAnomaly ? "#ef4444" : stroke}
      stroke="#111"
      strokeWidth={1}
    />
  );
};

function transformData(data: MarketAnomaliesSeries[] | undefined) {
  if (!data) return [];

  const map = new Map<string, any>();

  for (const series of data) {
    if (series.target !== "price") continue;

    for (const point of series.signals) {
      map.set(point.date, {
        date: point.date,
        price: point.score,
        isHomeAnomaly: point.is_anomaly,
      });
    }
  }

  return [...map.values()].sort(
    (a, b) => new Date(a.date).getTime() - new Date(b.date).getTime()
  );
}

function MarketAnomaliesChart({ data }: MarketAnomaliesChartProps) {
  const transformedData = transformData(data);
  const customTicks = transformedData
    .filter((_, index) => index % 24 === 0)
    .map((d) => d.date);

  return (
    <ResponsiveContainer width="100%" height="100%">
      <LineChart data={transformedData}>
        <Line
          type="monotone"
          dataKey="price"
          stroke="#10b981"
          strokeWidth={2}
          connectNulls={true}
          dot={(props) => <AnomalyDot {...props} dataKey="price" />}
          activeDot={{ r: 6 }}
        />

        <XAxis
          dataKey="date"
          ticks={customTicks}
          interval={0}
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
          tickFormatter={(val) => val.toLocaleString("en-US")}
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
            value.toLocaleString("en-US"),
            props.payload.isHomeAnomaly ? "Home • Anomaly" : "Home",
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
