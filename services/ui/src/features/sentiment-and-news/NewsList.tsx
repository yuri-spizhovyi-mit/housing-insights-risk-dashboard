import NewsItem from "./NewsItem";
import type { CitySentiments } from "../../types/sentiments";
import { memo } from "react";

interface NewsListProps {
  data: CitySentiments | undefined;
}

function NewsList({ data }: NewsListProps) {
  return (
    <ul className="space-y-3">
      {data?.items.map((item, i) => (
        <NewsItem key={i} {...item} />
      ))}
    </ul>
  );
}

export default memo(NewsList);
