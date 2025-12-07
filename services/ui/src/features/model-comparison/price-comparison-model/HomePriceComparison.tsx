import Frame from "../../../ui/Frame";
import { useFilters } from "../../../context/FilterContext";
import Message from "../../../ui/Message";
import Skeleton from "@mui/material/Skeleton";
import { Home } from "lucide-react";
import { useMemo } from "react";
import { useModelComparison } from "../useModelComparison";
import HomePriceComparisonChart from "./HomePriceComparisonChart";

function HomePriceComparison() {
  const { city } = useFilters();
  const { modelsData, error, isFetching } = useModelComparison(city, "price");
  const memoizedData = useMemo(() => modelsData, [modelsData?.city]);

  return (
    <Frame className="col-span-12 sm:col-span-8 opacity-100 flex flex-col">
      {isFetching ? (
        <Skeleton
          variant="rounded"
          width="100%"
          height={30}
          animation="wave"
          className="mb-9"
        />
      ) : (
        <Frame.Header
          leftIcon={<Home className="size-5 opacity-80" />}
          title="Home Price Forecast Model Comparison"
        />
      )}

      <Frame.Body className="min-h-64 flex-1">
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
        ) : (
          <HomePriceComparisonChart modelsData={memoizedData} />
        )}
      </Frame.Body>
    </Frame>
  );
}

export default HomePriceComparison;
