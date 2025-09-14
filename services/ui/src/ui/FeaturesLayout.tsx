import type { ReactNode } from "react";

interface FeaturesLayoutProps {
  children: ReactNode;
}

function FeaturesLayout({ children }: FeaturesLayoutProps) {
  return <div className="px-6 py-6 grid grid-cols-12 gap-4">{children}</div>;
}

export default FeaturesLayout;
