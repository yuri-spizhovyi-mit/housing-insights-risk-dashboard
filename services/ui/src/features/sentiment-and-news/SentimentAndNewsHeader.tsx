import { Newspaper } from "lucide-react";

function SentimentAndNewsHeader() {
  return (
    <div className="flex items-center gap-2 mb-6">
      <Newspaper className="size-4 opacity-80" />
      <h2 className="font-semibold">Sentiment & News</h2>
    </div>
  );
}

export default SentimentAndNewsHeader;
