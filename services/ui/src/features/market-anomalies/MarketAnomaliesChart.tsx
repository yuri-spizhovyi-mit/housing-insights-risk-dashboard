import {
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
  type DotProps,
} from "recharts";
import type { MarketAnomaly } from "../../types/market-anomalies";

interface MarketAnomaliesChartProps {
  data: MarketAnomaly[] | undefined;
}

const CustomDot = (props: DotProps) => {
  const { cx, cy, payload } = props as DotProps & { payload: MarketAnomaly };
  if (payload?.is_anomaly) {
    return (
      <circle
        cx={cx}
        cy={cy}
        r={5}
        fill="#ef4444"
        stroke="#111"
        strokeWidth={1.5}
      />
    );
  }
  return null;
};

function MarketAnomaliesChart({ data }: MarketAnomaliesChartProps) {
  return (
    <ResponsiveContainer width="100%" height="100%">
      <LineChart
        data={data}
        margin={{ top: 20, right: 30, left: 20, bottom: 20 }}
      >
        <Line
          type="monotone"
          dataKey="score"
          stroke="#facc15"
          strokeWidth={2}
          dot={<CustomDot />}
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
          labelStyle={{ color: "#60a5fa" }}
          formatter={(value: number, _name: string, props: any) => [
            value.toFixed(2),
            props.payload.is_anomaly ? "Anomaly" : "Normal",
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

export default MarketAnomaliesChart;
