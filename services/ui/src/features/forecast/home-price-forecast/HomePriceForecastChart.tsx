import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import type { ForecastPoint } from "../../../types/forecast";
import { memo } from "react";

interface HomePriceForecastChartProps {
  data: ForecastPoint[] | undefined;
}

function HomePriceForecastChart({ data }: HomePriceForecastChartProps) {
  return (
    <ResponsiveContainer width="100%" height="100%">
      <LineChart
        data={data}
        margin={{ top: 20, right: 30, left: 20, bottom: 20 }}
      >
        <Line
          type="monotone"
          dataKey="value"
          stroke="#3b82f6"
          strokeWidth={2}
          dot={false}
        />
        <Line
          type="monotone"
          dataKey="upper"
          stroke="#22c55e"
          strokeDasharray="5 5"
          dot={false}
        />
        <Line
          type="monotone"
          dataKey="lower"
          stroke="#ef4444"
          strokeDasharray="5 5"
          dot={false}
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
          tickLine
          axisLine={{ stroke: "#333" }}
        />
        <YAxis
          tickFormatter={(val) => `$${val.toLocaleString()}`}
          tick={{
            fontSize: 12,
            fill: "var(--text-primary)",
            opacity: 0.7,
            dx: -4,
          }}
          tickLine
          axisLine={{ stroke: "#333" }}
        />
        <Tooltip
          contentStyle={{
            background: "#111",
            border: "1px solid #333",
            fontSize: "15px",
          }}
          labelStyle={{ color: "#ffffff" }}
          formatter={(value: number, name: string) => [
            `$${value.toLocaleString()}`,
            name === "upper"
              ? "Upper Price"
              : name === "lower"
              ? "Lower Price"
              : "Price",
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

export default memo(HomePriceForecastChart);
