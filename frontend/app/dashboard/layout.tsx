import { DashboardShell } from "@/components/layout/dashboard-shell";
import { RequireAuth } from "@/components/layout/require-auth";

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  return (
    <RequireAuth>
      <DashboardShell>{children}</DashboardShell>
    </RequireAuth>
  );
}
