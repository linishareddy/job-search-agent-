import { apiDelete, apiGet, apiPatch, apiPost, apiPut } from "@/lib/api/client";
import type { AtsCompany, AtsCompanyCreate, HealthStatus, Notification, SourceHealthMap } from "@/lib/types/misc";
import type { JobSearchResult, SearchResultsParams } from "@/lib/types/job";
import type {
  CreateFromTextPayload,
  CreateFromTextResult,
  ParsedSearchIntent,
  SavedSearch,
  SavedSearchCreate,
  SavedSearchUpdate,
} from "@/lib/types/search";

export const searchesApi = {
  list: () => apiGet<SavedSearch[]>("/searches"),
  get: (id: string) => apiGet<SavedSearch>(`/searches/${id}`),
  create: (data: SavedSearchCreate) => apiPost<SavedSearch>("/searches", data),
  update: (id: string, data: SavedSearchUpdate) => apiPut<SavedSearch>(`/searches/${id}`, data),
  delete: (id: string) => apiDelete(`/searches/${id}`),
  parseText: (text: string) => apiPost<ParsedSearchIntent>("/searches/parse-text", { text }),
  createFromText: (payload: CreateFromTextPayload) =>
    apiPost<CreateFromTextResult>("/searches/from-text", payload),
  run: (id: string) => apiPost<{ run_id: string }>(`/searches/${id}/run`),
  results: (id: string, params?: SearchResultsParams) =>
    apiGet<JobSearchResult[]>(`/searches/${id}/results`, {
      page: params?.page ?? 1,
      page_size: params?.page_size ?? 20,
      only_new: params?.only_new ? "true" : undefined,
      posted_within_days: params?.posted_within_days ?? undefined,
    }),
};

export const companiesApi = {
  list: () => apiGet<AtsCompany[]>("/companies"),
  create: (data: AtsCompanyCreate) => apiPost<AtsCompany>("/companies", data),
  delete: (id: string) => apiDelete(`/companies/${id}`),
};

export const notificationsApi = {
  list: (unreadOnly = false) =>
    apiGet<Notification[]>("/notifications", { unread_only: unreadOnly ? "true" : undefined }),
  markRead: (id: string) => apiPatch(`/notifications/${id}/read`),
  delete: (id: string) => apiDelete(`/notifications/${id}`),
};

export const healthApi = {
  check: () => apiGet<HealthStatus>("/health"),
  sources: () => apiGet<SourceHealthMap>("/health/sources"),
};
