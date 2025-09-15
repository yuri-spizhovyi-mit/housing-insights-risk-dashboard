import {
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

interface RentChart {
  data: Array<{ date: string; value: number }>;
}

function RentForecastChart({ data }: RentChart) {
  return (
    <div className="h-64">
      <ResponsiveContainer width="95%" height="100%">
        <LineChart data={data}>
          <Line
            type="monotone"
            dataKey="value"
            stroke="#34d399"
            strokeWidth={2}
            dot={false}
          />
          <XAxis
            dataKey="date"
            tick={{ fontSize: 12, fill: "#a3a3a3", dy: 12 }}
            tickLine={true}
            axisLine={{ stroke: "#333" }}
          />
          <YAxis
            tick={{ fontSize: 12, fill: "#a3a3a3", dx: -12 }}
            tickLine={true}
            axisLine={{ stroke: "#333" }}
          />
          <Tooltip
            labelStyle={{ color: "#34d399" }}
            contentStyle={{
              background: "#111",
              border: "1px solid #a3a3a3",
              fontSize: "15px",
            }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

export default RentForecastChart;
