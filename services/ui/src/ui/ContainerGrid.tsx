import type { ReactNode } from "react";

interface ContainerGridProps {
  children: ReactNode;
}

function ContainerGrid({ children }: ContainerGridProps) {
  return <div className="px-6 py-6 grid grid-cols-12 gap-4">{children}</div>;
}

export default ContainerGrid;
