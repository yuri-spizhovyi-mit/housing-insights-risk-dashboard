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
    <section className="col-span-12 lg:col-span-4 rounded-2xl border border-neutral-800 bg-neutral-900 p-4">
      <SentimentAndNewsHeader />
      <ul className="space-y-3">
        {newsItems.map((item, i) => (
          <NewsItem key={i} {...item} />
        ))}
      </ul>
    </section>
  );
}

export default SentimentAndNews;
