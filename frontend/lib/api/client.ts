import { ApiError, type ApiErrorBody, type ApiResponse } from "@/lib/types/api";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

export function getApiBaseUrl(): string {
  return API_URL;
}

async function parseError(res: Response): Promise<ApiError> {
  let body: ApiErrorBody | undefined;
  try {
    body = await res.json();
  } catch {
    /* empty */
  }
  const message =
    body?.message ??
    (typeof body?.detail === "string" ? body.detail : undefined) ??
    `Request failed (${res.status})`;
  return new ApiError(message, res.status, body);
}

export async function apiRequest<T>(
  path: string,
  options: RequestInit = {}
): Promise<ApiResponse<T>> {
  const url = `${API_URL}${path.startsWith("/") ? path : `/${path}`}`;
  const headers: HeadersInit = {
    "Content-Type": "application/json",
    ...(options.headers ?? {}),
  };

  const res = await fetch(url, { ...options, headers });

  if (!res.ok) {
    throw await parseError(res);
  }

  if (res.status === 204) {
    return { success: true };
  }

  return res.json() as Promise<ApiResponse<T>>;
}

export async function apiGet<T>(path: string, params?: Record<string, string | number | boolean | undefined | null>): Promise<ApiResponse<T>> {
  const search = new URLSearchParams();
  if (params) {
    Object.entries(params).forEach(([k, v]) => {
      if (v !== undefined && v !== null && v !== "") {
        search.set(k, String(v));
      }
    });
  }
  const qs = search.toString();
  return apiRequest<T>(qs ? `${path}?${qs}` : path);
}

export async function apiPost<T>(path: string, body?: unknown): Promise<ApiResponse<T>> {
  return apiRequest<T>(path, {
    method: "POST",
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });
}

/** For the one endpoint (cover-letter generation) that streams plain-text tokens
 * instead of the usual JSON envelope — everything else should use apiPost. */
export async function apiPostStream(path: string, body: unknown): Promise<ReadableStream<Uint8Array>> {
  const url = `${API_URL}${path.startsWith("/") ? path : `/${path}`}`;
  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });

  if (!res.ok) {
    throw await parseError(res);
  }
  if (!res.body) {
    throw new ApiError("No response body", res.status);
  }
  return res.body;
}

export async function apiPostForm<T>(path: string, formData: FormData): Promise<ApiResponse<T>> {
  const url = `${API_URL}${path.startsWith("/") ? path : `/${path}`}`;
  const res = await fetch(url, { method: "POST", body: formData });

  if (!res.ok) {
    throw await parseError(res);
  }

  return res.json() as Promise<ApiResponse<T>>;
}

export async function apiPut<T>(path: string, body: unknown): Promise<ApiResponse<T>> {
  return apiRequest<T>(path, { method: "PUT", body: JSON.stringify(body) });
}

export async function apiPatch<T>(path: string, body?: unknown): Promise<ApiResponse<T>> {
  return apiRequest<T>(path, {
    method: "PATCH",
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });
}

export async function apiDelete(path: string): Promise<void> {
  await apiRequest(path, { method: "DELETE" });
}
