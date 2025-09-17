import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import Frame from "../../ui/Frame";
import HomePriceForecastHeader from "./HomePriceForecastHeader";

const staticData = [
  { date: "2025-1", value: 700 },
  { date: "2025-02", value: 710 },
  { date: "2025-03", value: 725 },
  { date: "2025-04", value: 730 },
  { date: "2025-05", value: 740 },
  { date: "2025-06", value: 755 },
  { date: "2025-07", value: 770 },
  { date: "2025-08", value: 785 },
  { date: "2025-09", value: 800 },
  { date: "2025-10", value: 810 },
  { date: "2025-11", value: 700 },
  { date: "2025-12", value: 700 },

  { date: "2026-01", value: 700 },
  { date: "2026-02", value: 710 },
  { date: "2026-03", value: 725 },
  { date: "2026-04", value: 730 },
  { date: "2026-05", value: 740 },
  { date: "2026-06", value: 755 },
  { date: "2026-07", value: 770 },
  { date: "2026-08", value: 785 },
  { date: "2026-09", value: 800 },
  { date: "2026-10", value: 810 },
  { date: "2026-11", value: 700 },
  { date: "2026-12", value: 700 },
];

function HomePriceForecast() {
  return (
    <Frame className="col-span-12 lg:col-span-8">
      <HomePriceForecastHeader />

      <div className="h-64">
        <ResponsiveContainer width="95%" height="100%">
          <LineChart data={staticData}>
            <Line
              type="monotone"
              dataKey="value"
              stroke="#60a5fa"
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
              contentStyle={{
                background: "#111",
                border: "1px solid #333",
                fontSize: "15px",
              }}
              labelStyle={{ color: "#60a5fa" }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </Frame>
  );
}

export default HomePriceForecast;
