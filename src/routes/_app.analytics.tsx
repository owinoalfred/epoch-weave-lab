import { createFileRoute } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { PageHeader } from "@/components/app/page-header";

export const Route = createFileRoute("/_app/analytics")({ component: Page });

function Page() {
  const wl = useQuery({ queryKey: ["wl"], queryFn: async () => (await api.get("/reports/workloads")).data });
  const ru = useQuery({ queryKey: ["ru"], queryFn: async () => (await api.get("/reports/room-utilization")).data });
  const cl = useQuery({ queryKey: ["cl"], queryFn: async () => (await api.get("/reports/clashes")).data });
  const sd = useQuery({ queryKey: ["sd"], queryFn: async () => (await api.get("/reports/student-days")).data });

  return (
    <div className="space-y-6">
      <PageHeader title="Analytics" description="Workloads, utilization, and conflict reports." />

      <div className="grid lg:grid-cols-2 gap-4">
        <Section title="Lecturer Workloads">
          <SimpleTable rows={wl.data ?? []} cols={[
            { k: "name", l: "Lecturer" }, { k: "rank", l: "Rank" },
            { k: "hours", l: "Hrs" }, { k: "max_hours", l: "Max" },
            { k: "utilization", l: "%", r: (x) => `${x.utilization}%` },
          ]} />
        </Section>
        <Section title="Room Utilization">
          <SimpleTable rows={ru.data ?? []} cols={[
            { k: "code", l: "Room" }, { k: "type", l: "Type" },
            { k: "capacity", l: "Cap" }, { k: "sessions", l: "Sessions" },
            { k: "utilization", l: "%", r: (x) => `${x.utilization}%` },
          ]} />
        </Section>
        <Section title="Student-Days per Group">
          <SimpleTable rows={sd.data ?? []} cols={[
            { k: "name", l: "Group" }, { k: "day_count", l: "Days" }, { k: "sessions", l: "Sessions" },
          ]} />
        </Section>
        <Section title="Clashes">
          <div className="text-sm">
            <div className="text-muted-foreground">Room: <span className="text-foreground">{(cl.data as any)?.room_clashes?.length ?? 0}</span></div>
            <div className="text-muted-foreground">Lecturer: <span className="text-foreground">{(cl.data as any)?.lecturer_clashes?.length ?? 0}</span></div>
          </div>
        </Section>
      </div>
    </div>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="glass rounded-xl p-5">
      <h3 className="font-semibold mb-3">{title}</h3>
      {children}
    </div>
  );
}

function SimpleTable({ rows, cols }: { rows: any[]; cols: { k: string; l: string; r?: (x: any) => any }[] }) {
  if (rows.length === 0) return <div className="text-sm text-muted-foreground">No data.</div>;
  return (
    <div className="max-h-80 overflow-y-auto">
      <table className="w-full text-xs">
        <thead className="text-muted-foreground uppercase tracking-wider">
          <tr>{cols.map((c) => <th key={c.k} className="text-left font-medium py-2">{c.l}</th>)}</tr>
        </thead>
        <tbody>
          {rows.map((r, i) => (
            <tr key={i} className="border-t border-border/40">
              {cols.map((c) => <td key={c.k} className="py-2 pr-2">{c.r ? c.r(r) : String(r[c.k] ?? "—")}</td>)}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
