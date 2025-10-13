import { AlertTriangle, Info } from "lucide-react";

interface MessageProps {
  type: "error" | "empty";
  message: string;
  details?: string;
}

function Message({ type, message, details }: MessageProps) {
  const isError = type === "error";

  return (
    <div
      className={`flex items-start gap-3 rounded-xl border p-4 text-sm shadow-md size-full transition-colors duration-300 ${
        isError
          ? "border-msg-error-border bg-msg-error-bg text-msg-error-text"
          : "border-msg-info-border bg-msg-info-bg text-msg-info-text"
      }`}
    >
      <div className="flex-shrink-0">
        {isError ? (
          <AlertTriangle className="h-5 w-5 text-msg-error-border" />
        ) : (
          <Info className="h-5 w-5 text-msg-info-border" />
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
