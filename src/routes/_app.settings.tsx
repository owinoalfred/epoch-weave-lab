import { createFileRoute } from "@tanstack/react-router";
import { useMutation } from "@tanstack/react-query";
import { toast } from "sonner";
import { PageHeader } from "@/components/app/page-header";
import { useAuth } from "@/lib/auth-store";
import { api, DEMO_MODE } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { RefreshCw, Database, Server } from "lucide-react";

export const Route = createFileRoute("/_app/settings")({ component: Page });

function Page() {
  const { user } = useAuth();
  const apiUrl = (import.meta.env.VITE_API_URL as string | undefined) ?? "in-browser demo backend";

  const reset = useMutation({
    mutationFn: async () => (await api.post("/admin/reset")).data,
    onSuccess: () => { toast.success("Demo data reset"); setTimeout(() => location.reload(), 400); },
  });

  return (
    <div className="space-y-6">
      <PageHeader title="Settings" description="System configuration and account info." />

      <div className="glass rounded-xl p-5 space-y-2 text-sm">
        <Row label="Signed in as" value={`${user?.first_name ?? ""} ${user?.last_name ?? ""} (${user?.username})`} />
        <Row label="Email" value={user?.email ?? "—"} />
        <Row label="Roles" value={(user?.roles ?? []).join(", ") || "—"} />
        <Row label="API endpoint" value={apiUrl} />
        <Row label="Mode" value={DEMO_MODE ? "Demo (in-browser mock)" : "Live (Django backend)"} />
      </div>

      {DEMO_MODE ? (
        <div className="glass rounded-xl p-5 text-sm space-y-3">
          <div className="flex items-center gap-2 font-semibold"><Database className="size-4 text-primary" /> Demo Mode</div>
          <p className="text-muted-foreground">
            All data lives in your browser's localStorage. Create, edit, delete entities, generate
            timetables, run approvals — everything works exactly as it would against the Django backend.
            To switch to the real Django backend, set <code className="text-primary">VITE_API_URL</code> in
            your env and rebuild.
          </p>
          <Button variant="secondary" onClick={() => reset.mutate()} disabled={reset.isPending}>
            <RefreshCw className="size-4" /> Reset demo data
          </Button>
        </div>
      ) : (
        <div className="glass rounded-xl p-5 text-sm space-y-2">
          <div className="flex items-center gap-2 font-semibold"><Server className="size-4 text-primary" /> Live Backend</div>
          <p className="text-muted-foreground">
            Connected to <code>{apiUrl}</code>. The Django REST + OR-Tools backend lives in <code>backend/</code>.
            Run it with <code>docker compose up</code> and seed demo data with{" "}
            <code>python manage.py seed_demo</code>. OpenAPI docs are at <code>/api/docs/</code>.
          </p>
        </div>
      )}

      <div className="glass rounded-xl p-5 text-sm">
        <h3 className="font-semibold mb-2">Demo accounts</h3>
        <table className="text-xs w-full">
          <thead className="text-muted-foreground"><tr><th className="text-left py-1">Username</th><th className="text-left">Password</th><th className="text-left">Role</th></tr></thead>
          <tbody>
            {[
              ["admin", "admin12345", "SUPER_ADMIN"],
              ["dean", "password123", "DEAN"],
              ["hod", "password123", "HOD"],
              ["officer", "password123", "TIMETABLE_OFFICER"],
              ["jdoe", "password123", "LECTURER"],
            ].map(([u, p, r]) => (
              <tr key={u} className="border-t border-border/40">
                <td className="py-1.5"><code>{u}</code></td>
                <td><code>{p}</code></td>
                <td className="text-muted-foreground">{r}</td>
              </tr>
            ))}
          </tbody>
        </table>
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
