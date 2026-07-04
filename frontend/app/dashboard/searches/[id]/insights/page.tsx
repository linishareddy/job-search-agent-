"use client";

import { Suspense } from "react";
import { useParams } from "next/navigation";
import { SearchInsightsDashboard } from "@/components/dashboard/search-insights-dashboard";

function SearchInsightsContent() {
  const { id } = useParams<{ id: string }>();
  return <SearchInsightsDashboard searchId={id} />;
}

export default function SearchInsightsPage() {
  return (
    <Suspense fallback={<div className="h-64 animate-pulse rounded-xl bg-muted" />}>
      <SearchInsightsContent />
    </Suspense>
  );
}
