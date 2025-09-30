import type { Indicator } from "../../types/risk.types";

type BreakdownListProps = {
  breakdown: Indicator[] | undefined;
};

export function BreakdownList({ breakdown }: BreakdownListProps) {
  return (
    <div className="flex-1 text-sm divide-y divide-neutral-700 w-full">
      {breakdown?.map((item) => (
        <div key={item.name} className="flex items-center justify-between py-4">
          <span className="opacity-80">{item.name}</span>
          <span className="rounded-full px-2 py-0.5 text-xs bg-neutral-800 text-neutral-200">
            {item.status}
          </span>
        </div>
      ))}
    </div>
  );
}
