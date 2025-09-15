import type { ReactNode } from "react";

interface FrameProps {
  children: ReactNode;
  className: string;
}
//col-span-12 lg:col-span-8
function Frame({ children, className }: FrameProps) {
  return (
    <div
      className={`rounded-2xl border border-neutral-800 bg-neutral-900 p-4 ${className}`}
    >
      {children}
    </div>
  );
}

export default Frame;
