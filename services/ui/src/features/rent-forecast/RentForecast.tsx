import {
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import Frame from "../../ui/Frame";
import RentForecastHeader from "./RentForecastHeader";

import { useForecast } from "../../hooks/useForecast";
import { useFilters } from "../../context/FilterContext";
import Message from "../../ui/Message";

function RentForecast() {
  const filters = useFilters();
  const { forecast, error, isFetching } = useForecast(filters, "rent");

  return (
    <Frame className="col-span-12 lg:col-span-8">
      <RentForecastHeader />

      {error ? (
        <Message
          type={error.type}
          message={error.message}
          details={error.details}
        />
      ) : isFetching ? (
        <p className="text-gray-400">Fetching forecast…</p>
      ) : (
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart
              data={forecast?.data ?? []}
              margin={{ top: 20, right: 30, left: 20, bottom: 20 }}
            >
              <Line
                type="monotone"
                dataKey="value"
                stroke="#60a5fa"
                strokeWidth={2}
                dot={false}
              />
              <Line
                type="monotone"
                dataKey="lower"
                stroke="#34d399"
                strokeDasharray="5 5"
                dot={false}
              />
              <Line
                type="monotone"
                dataKey="upper"
                stroke="#34d399"
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
                tick={{ fontSize: 12, fill: "#a3a3a3", dy: 12 }}
                tickLine
                axisLine={{ stroke: "#333" }}
              />
              <YAxis
                tickFormatter={(val) => `$${val.toLocaleString()}`}
                tick={{ fontSize: 12, fill: "#a3a3a3", dx: -4 }}
                tickLine
                axisLine={{ stroke: "#333" }}
              />
              <Tooltip
                contentStyle={{
                  background: "#111",
                  border: "1px solid #333",
                  fontSize: "15px",
                }}
                labelStyle={{ color: "#60a5fa" }}
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
        </div>
      )}
    </Frame>
  );
}

export default RentForecast;
