export const WORK_MODE_OPTIONS = ["any", "remote", "hybrid", "onsite"].map((v) => ({
  label: v.charAt(0).toUpperCase() + v.slice(1),
  value: v,
}));

export const EXPERIENCE_LEVEL_OPTIONS = ["any", "entry", "mid", "senior", "lead"].map((v) => ({
  label: v.charAt(0).toUpperCase() + v.slice(1),
  value: v,
}));

// The default "posted within N days" filter saved on a search and applied
// server-side unless overridden per-request (see POSTED_RESULT_FILTERS below).
export const POSTED_WITHIN_OPTIONS = [
  { label: "All time", value: 0 },
  { label: "7 days", value: 7 },
  { label: "14 days", value: 14 },
  { label: "30 days", value: 30 },
] as const;

// Deliberately more granular than POSTED_WITHIN_OPTIONS: this filters jobs already
// fetched for one search's results, not the search's saved default, so finer-grained
// options (1d, 90d) are useful here in a way they aren't for the saved default.
export const POSTED_RESULT_FILTERS = [
  { label: "All", value: -1 },
  { label: "1d", value: 1 },
  { label: "7d", value: 7 },
  { label: "30d", value: 30 },
  { label: "90d", value: 90 },
] as const;
