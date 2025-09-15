interface NewsItemProps {
  title: string;
  tone: "pos" | "neg" | "neu";
  date: string;
}

function NewsItem({ title, tone, date }: NewsItemProps) {
  const toneClasses =
    tone === "pos"
      ? "border-emerald-400 text-emerald-300"
      : tone === "neg"
      ? "border-rose-400 text-rose-300"
      : "border-neutral-600 text-neutral-300";

  return (
    <li className="rounded-xl border border-neutral-800 p-3 bg-neutral-950">
      <div className="text-sm font-medium line-clamp-1 mb-2">{title}</div>
      <div className="text-xs opacity-60 mt-1 flex items-center gap-2">
        <span className={`rounded-full px-2 py-0.5 border ${toneClasses}`}>
          {tone.toUpperCase()}
        </span>
        <span>{date}</span>
      </div>
    </li>
  );
}

export default NewsItem;
