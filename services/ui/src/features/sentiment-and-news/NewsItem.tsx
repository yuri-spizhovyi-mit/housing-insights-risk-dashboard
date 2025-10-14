import type { Sentiment, SentimentValue } from "../../types/sentiments";

const toneClasses = {
  POS: `
    bg-tone-pos-bg
    border-tone-pos-border
    text-tone-pos-text
  `,
  NEG: `
    bg-tone-neg-bg
    border-tone-neg-border
    text-tone-neg-text
  `,
  NEU: `
    bg-tone-neu-bg
    border-tone-neu-border
    text-tone-neu-text
  `,
};

function NewsItem({ headline, sentiment, date }: Sentiment) {
  const formatedSentiment = sentiment.toUpperCase() as SentimentValue;
  return (
    <li className="rounded-xl border border-neutral-800 p-3 bg-sentiment-bg">
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
