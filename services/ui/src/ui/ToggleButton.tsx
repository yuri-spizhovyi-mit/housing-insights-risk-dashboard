import { useEffect, useState } from "react";
import { Sun, Moon } from "lucide-react";

function ThemeToggle() {
  const [isDark, setIsDark] = useState(false);

  useEffect(() => {
    document.documentElement.classList.toggle("dark", isDark);
  }, [isDark]);

  return (
    <button
      onClick={() => setIsDark((prev) => !prev)}
      className={`
        relative w-16 h-8 rounded-full flex items-center transition-colors duration-500
        ${
          isDark
            ? "bg-gradient-to-r from-indigo-800 via-blue-900 to-gray-900"
            : "bg-gradient-to-r from-sky-200 via-sky-400 to-sky-300"
        }
      `}
    >
      <div
        className={`
          absolute w-6 h-6 rounded-full flex items-center justify-center transition-all duration-500 ease-in-out
          ${
            isDark
              ? "translate-x-2 bg-slate-200 shadow-[0_0_8px_#60a5fa]"
              : "translate-x-8 bg-yellow-300 shadow-[0_0_8px_#facc15]"
          }
        `}
      >
        {isDark ? (
          <Moon className="w-4 h-4 text-sky-400" />
        ) : (
          <Sun className="w-4 h-4 text-amber-600" />
        )}
      </div>
    </button>
  );
}

export default ThemeToggle;
