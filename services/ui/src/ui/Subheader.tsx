import { Info } from "lucide-react";

function Subheader() {
  return (
    <div className="px-8 bg-gradient-to-r from-purple-900 via-blue-900 to-indigo-900 border-b border-purple-700 py-3">
      <div className="flex items-center justify-center gap-3">
        <Info className="size-4 text-cyan-300 inline-block" />
        <p className="text-cyan-50 text-sm">
          Read more about team and project development{" "}
          <a
            href="#"
            className="text-cyan-300 hover:text-cyan-200 underline underline-offset-2 transition-colors font-medium"
          >
            here
          </a>
        </p>
      </div>
    </div>
  );
}

export default Subheader;
