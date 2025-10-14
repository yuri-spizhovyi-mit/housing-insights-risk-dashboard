import { useRef, useEffect, useState } from "react";
import Lenis from "lenis";
import { LenisContext } from "./LenisContextObject";

export function LenisProvider({ children }: { children: React.ReactNode }) {
  const lenisRef = useRef<Lenis | null>(null);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    if (!lenisRef.current) {
      lenisRef.current = new Lenis({
        duration: 1.2,
        orientation: "vertical",
        smoothWheel: true,
        wheelMultiplier: 2,
        touchMultiplier: 2,
        infinite: false,
      });
      function raf(time: number) {
        lenisRef.current?.raf(time);
        requestAnimationFrame(raf);
      }
      requestAnimationFrame(raf);
    }
    setReady(true);

    return () => {
      lenisRef.current?.destroy();
    };
  }, []);

  if (!ready || !lenisRef.current) return null;

  return (
    <LenisContext.Provider value={lenisRef.current}>
      {children}
    </LenisContext.Provider>
  );
}
