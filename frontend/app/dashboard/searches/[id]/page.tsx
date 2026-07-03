import { Suspense } from "react";
import SearchDetailPage from "./search-detail-client";

export default function Page() {
  return (
    <Suspense fallback={<div className="h-64 animate-pulse rounded-xl bg-muted" />}>
      <SearchDetailPage />
    </Suspense>
  );
}
