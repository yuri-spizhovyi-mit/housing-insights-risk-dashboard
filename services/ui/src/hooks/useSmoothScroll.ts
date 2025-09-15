import { useEffect } from "react";
import Lenis from "lenis";

export function useSmoothScroll() {
  useEffect(() => {
    const lenis = new Lenis({
      duration: 1.2, // Controls how smooth the scrolling is (higher = smoother but slower)
      orientation: "vertical", // Scroll direction: "vertical" | "horizontal" | "both"
      smoothWheel: true, // Enable smooth mouse wheel scrolling (creates buttery smooth feel)
      wheelMultiplier: 2, // Prover of scrolling mouse wheel
      touchMultiplier: 2, // Touch/mobile scroll sensitivity: 1.0 = normal, 2.0 = sensitive, 3.0 = very sensitive
      infinite: false,
    });

    function raf(time: number) {
      lenis.raf(time);
      requestAnimationFrame(raf);
    }
    requestAnimationFrame(raf);

    return () => {
      lenis.destroy();
    };
  }, []);
}
