import type { Sentiment, SentimentValue } from "../../types/sentiments.types";

const toneClasses = {
  POS: "border-emerald-400 text-emerald-300",
  NEG: "border-rose-400 text-rose-300",
  NEU: "border-neutral-600 text-neutral-300",
};

function NewsItem({ headline, sentiment, date }: Sentiment) {
  const formatedSentiment = sentiment.toUpperCase() as SentimentValue;
  return (
    <li className="rounded-xl border border-neutral-800 p-3 bg-neutral-950">
      <div className="text-sm font-medium line-clamp-1 mb-2">{headline}</div>
      <div className="text-xs opacity-60 mt-1 flex items-center gap-2">
        <span
          className={`rounded-full px-2 py-0.5 border ${toneClasses[formatedSentiment]}`}
        >
          {formatedSentiment}
        </span>
        <span>{date}</span>
      </div>
    </li>
  );
}

export default NewsItem;
