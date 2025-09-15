import Frame from "../../ui/Frame";
import NewsItem from "./NewsItem";
import SentimentAndNewsHeader from "./SentimentAndNewsHeader";

function SentimentAndNews() {
  const newsItems: Array<{
    title: string;
    tone: "pos" | "neg" | "neu";
    date: string;
  }> = [
    {
      title: "Kelowna rental demand rises",
      tone: "pos",
      date: "2025-07-28",
    },
    {
      title: "Rate cuts delayed; affordability worsens",
      tone: "neg",
      date: "2025-08-14",
    },
    {
      title: "New supply targets announced",
      tone: "neu",
      date: "2025-08-29",
    },
  ];

  return (
    <Frame className="col-span-12 lg:col-span-4 text-amber-50">
      <SentimentAndNewsHeader />
      <ul className="space-y-3">
        {newsItems.map((item, i) => (
          <NewsItem key={i} {...item} />
        ))}
      </ul>
    </Frame>
  );
}

export default SentimentAndNews;
