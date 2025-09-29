import { AlertTriangle, Info } from "lucide-react";

interface MessageProps {
  type: "error" | "empty";
  message: string;
  details?: string;
}

function Message({ type, message, details }: MessageProps) {
  const isError = type === "error";
  console.log(type);

  return (
    <div
      className={`flex items-start gap-3 rounded-xl border p-4 text-sm shadow-md ${
        isError
          ? "border-red-400/40 bg-red-900/30 text-red-200"
          : "border-blue-400/30 bg-blue-900/20 text-blue-200"
      }`}
    >
      <div className="flex-shrink-0">
        {isError ? (
          <AlertTriangle className="h-5 w-5 text-red-400" />
        ) : (
          <Info className="h-5 w-5 text-blue-300" />
        )}
      </div>
      <div>
        <p className="font-semibold">{message}</p>
        {details && <p className="mt-1 text-sm opacity-90">{details}</p>}
      </div>
    </div>
  );
}

export default Message;
