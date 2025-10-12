import Frame from "../../ui/Frame";

function UiOverview() {
  return (
    <Frame className="col-span-12 lg:col-span-4">
      <Frame.Header title="UI Overview" />

      <Frame.Body className="pl-5 pb-2 text-sm">
        <ul className="list-disc space-y-3">
          <li>
            <strong>Home Price Forecast:</strong> Displays predicted sale prices
            over time using macro (Prophet) and micro (LGBM) models.
          </li>
          <li>
            <strong>Rent Price Forecast:</strong> Shows median rent trends, with
            overlays from macro and micro prediction models.
          </li>
          <li>
            <strong>Market Anomalies:</strong> Detects unusual price movements
            using the Isolation Forest algorithm.
          </li>
          <li>
            <strong>Risk Gauge:</strong> Combines affordability, inventory, and
            macro indicators into a single index.
          </li>
          <li>
            <strong>Sentiment & News:</strong> Extracts recent headlines and
            tones from local housing market reports.
          </li>
          <li>
            <strong>Predict Button:</strong> Updates all charts by fetching data
            from FastAPI endpoints: <code>/forecast</code>, <code>/micro</code>,{" "}
            <code>/anomalies</code>.
          </li>
        </ul>
      </Frame.Body>
    </Frame>
  );
}

export default UiOverview;
