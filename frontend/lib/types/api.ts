export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  message?: string;
  total?: number;
  page?: number;
  page_size?: number;
}

export interface ApiErrorBody {
  success?: boolean;
  message?: string;
  detail?: string | { msg: string; loc: string[] }[];
}

export class ApiError extends Error {
  status: number;
  body?: ApiErrorBody;

  constructor(message: string, status: number, body?: ApiErrorBody) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.body = body;
  }
}

export function parseApiError(err: unknown): string {
  if (err instanceof ApiError) {
    if (err.body?.detail && Array.isArray(err.body.detail)) {
      return err.body.detail.map((d) => d.msg).join(", ");
    }
    return err.message;
  }
  if (err instanceof Error) return err.message;
  return "Something went wrong";
}
