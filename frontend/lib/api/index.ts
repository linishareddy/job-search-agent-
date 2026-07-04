import { apiDelete, apiGet, apiPatch, apiPost, apiPostForm, apiPostStream } from "@/lib/api/client";
import type { AtsCompany, AtsCompanyCreate, HealthStatus, Notification, SourceHealthMap } from "@/lib/types/misc";
import type { JobSearchResult, SearchResultsParams } from "@/lib/types/job";
import type { ApplicationStatus, JobApplication } from "@/lib/types/application";
import type { GlobalAnalytics, SearchAnalytics } from "@/lib/types/analytics";
import type { CoverLetterFromResumePayload, ExtractedResumeText, Resume, ResumeDetail } from "@/lib/types/resume";
import type {
  CreateFromTextPayload,
  CreateFromTextResult,
  ParsedSearchIntent,
  RunStatus,
  SavedSearch,
  SavedSearchCreate,
  SavedSearchUpdate,
} from "@/lib/types/search";

export const searchesApi = {
  list: () => apiGet<SavedSearch[]>("/searches"),
  get: (id: string) => apiGet<SavedSearch>(`/searches/${id}`),
  create: (data: SavedSearchCreate) => apiPost<SavedSearch>("/searches", data),
  update: (id: string, data: SavedSearchUpdate) => apiPatch<SavedSearch>(`/searches/${id}`, data),
  delete: (id: string) => apiDelete(`/searches/${id}`),
  bulkDelete: (payload: { ids?: string[]; only_paused?: boolean }) =>
    apiPost<{ deleted: number }>("/searches/bulk-delete", payload),
  parseText: (text: string) => apiPost<ParsedSearchIntent>("/searches/parse-text", { text }),
  createFromText: (payload: CreateFromTextPayload) =>
    apiPost<CreateFromTextResult>("/searches/from-text", payload),
  run: (id: string) => apiPost<{ run_id: string }>(`/searches/${id}/run`),
  runStatus: (id: string) => apiGet<RunStatus>(`/searches/${id}/run-status`),
  analytics: (id: string, postedWithinDays?: number) =>
    apiGet<SearchAnalytics>(`/searches/${id}/analytics`, {
      posted_within_days: postedWithinDays,
    }),
  results: (id: string, params?: SearchResultsParams) =>
    apiGet<JobSearchResult[]>(`/searches/${id}/results`, {
      page: params?.page ?? 1,
      page_size: params?.page_size ?? 20,
      only_new: params?.only_new ? "true" : undefined,
      posted_within_days: params?.posted_within_days ?? undefined,
      resume_id: params?.resume_id ?? undefined,
    }),
};

export const analyticsApi = {
  overview: (activeOnly = false) =>
    apiGet<GlobalAnalytics>("/analytics/overview", {
      active_only: activeOnly ? "true" : undefined,
    }),
};

export const applicationsApi = {
  list: () => apiGet<JobApplication[]>("/applications"),
  create: (jobId: string) => apiPost<JobApplication>("/applications", { job_id: jobId }),
  update: (id: string, data: { status?: ApplicationStatus; notes?: string }) =>
    apiPatch<JobApplication>(`/applications/${id}`, data),
  delete: (id: string) => apiDelete(`/applications/${id}`),
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

export const resumesApi = {
  list: () => apiGet<Resume[]>("/resumes"),
  get: (id: string) => apiGet<ResumeDetail>(`/resumes/${id}`),
  upload: (file: File) => {
    const formData = new FormData();
    formData.append("file", file);
    return apiPostForm<Resume>("/resumes", formData);
  },
  delete: (id: string) => apiDelete(`/resumes/${id}`),
  extractText: (file: File) => {
    const formData = new FormData();
    formData.append("file", file);
    return apiPostForm<ExtractedResumeText>("/resumes/extract-text", formData);
  },
  coverLetterStream: (resumeId: string, payload: CoverLetterFromResumePayload) =>
    apiPostStream(`/resumes/${resumeId}/cover-letter`, payload),
};

export const healthApi = {
  check: () => apiGet<HealthStatus>("/health"),
  sources: () => apiGet<SourceHealthMap>("/health/sources"),
};
