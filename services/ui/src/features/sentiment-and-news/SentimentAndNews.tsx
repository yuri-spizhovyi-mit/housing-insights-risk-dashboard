import { useFilters } from "../../context/FilterContext";
import Frame from "../../ui/Frame";
import Message from "../../ui/Message";
import NewsItem from "./NewsItem";
import SentimentAndNewsHeader from "./SentimentAndNewsHeader";
import { useSentiments } from "./useSentiments";

function SentimentAndNews() {
  const { city } = useFilters();
  const { sentiments, error, isFetching } = useSentiments(city);

  return (
    <Frame className="col-span-12 lg:col-span-4 text-amber-50">
      {error ? (
        <Message
          type={error.type}
          message={error.message}
          details={error.details}
        />
      ) : (
        <>
          <SentimentAndNewsHeader />
          <ul className="space-y-3">
            {isFetching ? (
              <p>Pending..</p>
            ) : (
              sentiments?.items.map((item, i) => <NewsItem key={i} {...item} />)
            )}
          </ul>
        </>
      )}
    </Frame>
  );
}

export default SentimentAndNews;
