import { redirect } from "next/navigation";

export default async function AnalyticsPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  redirect(`/dashboard/searches/${id}/insights`);
}
