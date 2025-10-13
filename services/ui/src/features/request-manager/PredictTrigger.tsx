import { useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { TrendingUp } from "lucide-react";
import Button from "../../ui/Button";

function PredictTrigger() {
  const queryClient = useQueryClient();
  const [pos, setPos] = useState({ x: 50, y: 50 });
  const [hovered, setHovered] = useState(false);

  function runPrediction() {
    queryClient.invalidateQueries();
  }

  return (
    <Button
      onClick={runPrediction}
      onMouseMove={(e) => {
        const rect = e.currentTarget.getBoundingClientRect();
        setPos({
          x: ((e.clientX - rect.left) / rect.width) * 100,
          y: ((e.clientY - rect.top) / rect.height) * 100,
        });
      }}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      leftIcon={<TrendingUp className="w-4 h-4" />}
      className={`
        relative ml-4 px-6 py-2 rounded-xl
        text-sm font-semibold
        overflow-hidden transition-all duration-300
        bg-[linear-gradient(135deg,#10b981,#14b8a6,#06b6d4)]
        shadow-lg shadow-emerald-900/40
        hover:scale-[1.03] active:scale-[0.97]
        dark:text-white text-gray-900
      `}
      style={
        {
          "--x": `${pos.x}%`,
          "--y": `${pos.y}%`,
        } as React.CSSProperties
      }
    >
      <span
        className={`
          pointer-events-none absolute inset-0 rounded-xl
          opacity-0 transition-opacity duration-300
          ${hovered ? "opacity-100" : ""}
        `}
        style={{
          background: `radial-gradient(circle at var(--x) var(--y),
            rgba(255,255,255,0.25), transparent 40%)`,
        }}
      />
      Predict
    </Button>
  );
}

export default PredictTrigger;
