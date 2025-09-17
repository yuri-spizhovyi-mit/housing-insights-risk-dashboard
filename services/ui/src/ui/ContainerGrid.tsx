import gsap from "gsap";
import { useEffect, type ReactNode } from "react";

interface ContainerGridProps {
  children: ReactNode;
}

function ContainerGrid({ children }: ContainerGridProps) {
  useEffect(function () {
    gsap.fromTo(
      ".data-frame",
      { opacity: 0, y: 40, rotateX: -10 },
      {
        duration: 1,
        opacity: 1,
        y: 0,
        rotateX: 0,
        stagger: 0.25,
      }
    );
  }, []);

  return (
    <div className="px-6 py-6 grid grid-cols-12 gap-4 perspective-distant">
      {children}
    </div>
  );
}

export default ContainerGrid;
