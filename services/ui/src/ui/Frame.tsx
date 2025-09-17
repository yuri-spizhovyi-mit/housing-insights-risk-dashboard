import type { ReactNode } from "react";

interface FrameProps {
  children: ReactNode;
  className: string;
}
function Frame({ children, className }: FrameProps) {
  return (
    <div
      className={`data-frame opacity-0 rounded-2xl border text-amber-50 border-neutral-800 bg-neutral-900 p-4 ${className}`}
    >
      {children}
    </div>
  );
}

export default Frame;
