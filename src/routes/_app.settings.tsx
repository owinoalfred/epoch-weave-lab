import { createFileRoute } from "@tanstack/react-router";
import { PageHeader } from "@/components/app/page-header";
import { useAuth } from "@/lib/auth-store";

export const Route = createFileRoute("/_app/settings")({ component: Page });

function Page() {
  const { user } = useAuth();
  const apiUrl = (import.meta.env.VITE_API_URL as string | undefined) ?? "http://localhost:8000/api";
  return (
    <div className="space-y-6">
      <PageHeader title="Settings" description="System configuration and account info." />
      <div className="glass rounded-xl p-5 space-y-2 text-sm">
        <Row label="Signed in as" value={`${user?.first_name ?? ""} ${user?.last_name ?? ""} (${user?.username})`} />
        <Row label="Email" value={user?.email ?? "—"} />
        <Row label="Roles" value={(user?.roles ?? []).join(", ") || "—"} />
        <Row label="API endpoint" value={apiUrl} />
      </div>
      <div className="glass rounded-xl p-5 text-sm space-y-2">
        <h3 className="font-semibold mb-2">Backend</h3>
        <p className="text-muted-foreground">
          This frontend talks to the Django REST backend in <code>backend/</code>. Run it with{" "}
          <code>docker compose up</code> and seed demo data with{" "}
          <code>python manage.py seed_demo</code>. OpenAPI docs are at <code>/api/docs/</code>.
        </p>
      </div>
    </div>
  );
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between gap-4 border-b border-border/40 last:border-0 py-2">
      <div className="text-muted-foreground">{label}</div>
      <div className="font-medium text-right">{value}</div>
    </div>
  );
}
