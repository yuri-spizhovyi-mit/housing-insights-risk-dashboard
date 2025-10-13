import type { ReactNode } from "react";

interface SelectorShellProps {
  children: ReactNode;
  leftIcon?: ReactNode;
  type?: string;
  className?: string;
}

function SelectorShell({
  children,
  leftIcon,
  type,
  className,
}: SelectorShellProps) {
  return (
    <div
      className={`${className} flex items-center gap-4 rounded-2xl border border-neutral-700 py-3 shadow-lg`}
    >
      {type && (
        <div className="flex items-center gap-2">
          {leftIcon}
          <p className="text-sm opacity-70">{type}</p>
        </div>
      )}

      {children}
    </div>
  );
}

export default SelectorShell;
