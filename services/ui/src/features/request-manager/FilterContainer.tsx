import type { ReactNode } from "react";

interface FilterContainerProps {
  children: ReactNode;
}

function FilterContainer({ children }: FilterContainerProps) {
  return (
    <div className="grid gap-4 w-full text-primary sm:grid-cols-2 md:grid-cols-2 lg:flex lg:flex-wrap lg:items-center">
      {children}
    </div>
  );
}

export default FilterContainer;
