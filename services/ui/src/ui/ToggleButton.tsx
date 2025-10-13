import { useEffect, useState } from "react";
import { Sun, Moon } from "lucide-react";

function ThemeToggle() {
  const [isLight, setIsLight] = useState(true);

  useEffect(() => {
    document.documentElement.classList.toggle("light", isLight);
  }, [isLight]);

  return (
    <button
      onClick={() => setIsLight((prev) => !prev)}
      className={`
        relative w-16 h-8 rounded-full flex items-center transition-colors duration-500
        ${
          isLight
            ? "bg-gradient-to-r from-sky-200 via-sky-400 to-sky-300"
            : "bg-gradient-to-r from-indigo-800 via-blue-900 to-gray-900"
        }
      `}
    >
      <div
        className={`
          absolute w-6 h-6 rounded-full flex items-center justify-center transition-all duration-500 ease-in-out
          ${
            isLight
              ? "translate-x-8 bg-yellow-300 shadow-[0_0_8px_#facc15]"
              : "translate-x-2 bg-slate-200 shadow-[0_0_8px_#60a5fa]"
          }
        `}
      >
        {isLight ? (
          <Sun className="w-4 h-4 text-amber-600" />
        ) : (
          <Moon className="w-4 h-4 text-sky-400" />
        )}
      </div>
    </button>
  );
}

export default ThemeToggle;
