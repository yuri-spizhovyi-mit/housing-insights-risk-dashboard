interface ErrorMessageProps {
  message: string;
}

function ErrorMessage({ message }: ErrorMessageProps) {
  return (
    <div className="rounded-lg border border-red-500 bg-red-950/30 p-3 text-sm text-red-300">
      <p className="font-medium">⚠️ Oops, something went wrong</p>
      <p className="mt-1">{message}</p>
    </div>
  );
}

export default ErrorMessage;
