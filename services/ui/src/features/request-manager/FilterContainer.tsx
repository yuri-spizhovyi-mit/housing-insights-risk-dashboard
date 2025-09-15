import type { ReactNode } from "react";

interface FilterContainerProps {
  children: ReactNode;
}

function FilterContainer({ children }: FilterContainerProps) {
  return (
    <div className="flex gap-4 items-center w-full flex-wrap">{children}</div>
  );
}

export default FilterContainer;
