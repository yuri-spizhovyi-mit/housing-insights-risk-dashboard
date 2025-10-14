import Skeleton from "@mui/material/Skeleton";
import { useFilters } from "../../context/FilterContext";
import Frame from "../../ui/Frame";
import Message from "../../ui/Message";
import { useSentiments } from "./useSentiments";
import { Newspaper } from "lucide-react";
import { useMemo } from "react";
import NewsList from "./NewsList";

function SentimentAndNews() {
  const { city } = useFilters();
  const { sentiments, error, isFetching } = useSentiments(city);
  const memoizedData = useMemo(() => sentiments, [sentiments]);

  return (
    <Frame className="col-span-12 lg:col-span-4 text-amber-50">
      {isFetching ? (
        <Skeleton
          variant="rounded"
          width="60%"
          height={28}
          animation="wave"
          className="mb-6"
        />
      ) : (
        <Frame.Header
          leftIcon={<Newspaper className="size-4" />}
          title="Sentiment & News"
        />
      )}

      <div className="h-64">
        {error ? (
          <Message
            type={error.type}
            message={error.message}
            details={error.details}
          />
        ) : (
          <>
            {isFetching ? (
              <ul className="space-y-3">
                {Array.from({ length: 3 }).map((_, i) => (
                  <li
                    key={i}
                    className="
                    p-4 rounded-xl border
                    border-sentiment-card-border
                    bg-sentiment-card-bg
                    transition-colors duration-300
                  "
                  >
                    <Skeleton
                      variant="text"
                      width="80%"
                      height={15}
                      animation="wave"
                    />
                    <div className="flex gap-3 mt-3">
                      <Skeleton
                        variant="rounded"
                        width={50}
                        height={15}
                        animation="wave"
                      />
                      <Skeleton
                        variant="text"
                        width={80}
                        height={15}
                        animation="wave"
                      />
                    </div>
                  </li>
                ))}
              </ul>
            ) : (
              <NewsList data={memoizedData} />
            )}
          </>
        )}
      </div>
    </Frame>
  );
}

export default SentimentAndNews;
