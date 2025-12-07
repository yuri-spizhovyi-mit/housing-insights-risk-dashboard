import Frame from "../../ui/Frame";
import { useFilters } from "../../context/FilterContext";
import Message from "../../ui/Message";
import Skeleton from "@mui/material/Skeleton";
import { useModelComparison } from "../model-comparison/useModelComparison";
import type { ForecastTarget } from "../../services/dashboard";

const MODEL_LABELS = {
  arima: "ARIMA",
  prophet: "Prophet",
  lstm: "LSTM",
} as const;

const MODEL_COLORS = {
  arima: "text-blue-400",
  prophet: "text-green-400",
  lstm: "text-pink-400",
} as const;

export default function ComparisonSummaryTable({
  title,
  target,
}: {
  title: string;
  target: ForecastTarget;
}) {
  const { city } = useFilters();
  const { modelsData, isFetching, error } = useModelComparison(city, target);

  return (
    <Frame className="col-span-12 lg:col-span-4 flex flex-col">
      {isFetching ? (
        <Skeleton
          variant="rounded"
          width="100%"
          height={38}
          animation="wave"
          className="mb-9"
        />
      ) : (
        <Frame.Header title={title} />
      )}

      <Frame.Body className="min-h-40 h-full">
        {isFetching ? (
          <Skeleton
            variant="rounded"
            width="100%"
            height="100%"
            animation="wave"
          />
        ) : error ? (
          <Message
            type={error.type}
            message={error.message}
            details={error.details}
          />
        ) : !modelsData ? (
          <Message
            type="error"
            message="No model results available."
            details="Try switching city or adjusting filters."
          />
        ) : (
          <SummaryTableContent data={modelsData} />
        )}
      </Frame.Body>
    </Frame>
  );
}

function SummaryTableContent({
  data,
}: {
  data: NonNullable<ReturnType<typeof useModelComparison>["modelsData"]>;
}) {
  const { models, horizons } = data;

  const arima = models.arima ?? [];
  const prophet = models.prophet ?? [];
  const lstm = models.lstm ?? [];

  const metrics = ["mae", "mape", "rmse"] as const;

  const computeBest = (metric: (typeof metrics)[number]) => {
    const avg = {
      arima: arima.reduce((s, m) => s + (m[metric] ?? 0), 0) / horizons.length,
      prophet:
        prophet.reduce((s, m) => s + (m[metric] ?? 0), 0) / horizons.length,
      lstm: lstm.reduce((s, m) => s + (m[metric] ?? 0), 0) / horizons.length,
    };

    return Object.entries(avg).sort(
      (a, b) => a[1] - b[1]
    )[0][0] as keyof typeof MODEL_LABELS;
  };

  return (
    <table className="w-full text-left text-sm">
      <thead className="text-primary border-b">
        <tr>
          <th className="py-2">Metric</th>
          <th className="py-2">Best Model</th>
        </tr>
      </thead>

      <tbody className="text-primary">
        {metrics.map((metric) => {
          const best = computeBest(metric);
          return (
            <tr key={metric} className="border-gray-800">
              <td className="py-2 capitalize">{metric}</td>
              <td
                className={`py-2 font-semibold uppercase ${MODEL_COLORS[best]}`}
              >
                {MODEL_LABELS[best]}
              </td>
            </tr>
          );
        })}
      </tbody>
    </table>
  );
}
