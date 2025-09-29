export class ApiError extends Error {
  details: string;
  type: "error" | "empty";

  constructor(type: "error" | "empty", message: string, details: string) {
    super(message);
    this.type = type;
    this.details = details;
  }
}
