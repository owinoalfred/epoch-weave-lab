import { createFileRoute } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { Building2, GitBranch, GraduationCap, BookOpen, Users, DoorOpen, UsersRound, CalendarRange } from "lucide-react";
import { api } from "@/lib/api";
import { PageHeader } from "@/components/app/page-header";
import { StatCard } from "@/components/app/stat-card";
import { BarChart, Bar, XAxis, YAxis, ResponsiveContainer, Tooltip, Cell } from "recharts";

export const Route = createFileRoute("/_app/")({
  component: Dashboard,
});

interface Stats {
  faculties: number; departments: number; programmes: number; courses: number;
  lecturers: number; rooms: number; student_groups: number;
  timetables: number; published_timetables: number;
}

function Dashboard() {
  const { data, isLoading } = useQuery({
    queryKey: ["dashboard"],
    queryFn: async () => (await api.get<Stats>("/reports/dashboard")).data,
  });

  const workload = useQuery({
    queryKey: ["workloads"],
    queryFn: async () => (await api.get("/reports/workloads")).data as any[],
  });

  const rooms = useQuery({
    queryKey: ["room-util"],
    queryFn: async () => (await api.get("/reports/room-utilization")).data as any[],
  });

  return (
    <div className="space-y-6">
      <PageHeader
        title="Dashboard"
        description="Live operational view of your academic scheduling."
      />

      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <StatCard label="Faculties" value={data?.faculties ?? "—"} icon={<Building2 className="size-4" />} delay={0} />
        <StatCard label="Departments" value={data?.departments ?? "—"} icon={<GitBranch className="size-4" />} delay={0.04} />
        <StatCard label="Programmes" value={data?.programmes ?? "—"} icon={<GraduationCap className="size-4" />} delay={0.08} />
        <StatCard label="Courses" value={data?.courses ?? "—"} icon={<BookOpen className="size-4" />} delay={0.12} />
        <StatCard label="Lecturers" value={data?.lecturers ?? "—"} icon={<Users className="size-4" />} delay={0.16} />
        <StatCard label="Rooms" value={data?.rooms ?? "—"} icon={<DoorOpen className="size-4" />} delay={0.2} />
        <StatCard label="Student Groups" value={data?.student_groups ?? "—"} icon={<UsersRound className="size-4" />} delay={0.24} />
        <StatCard label="Timetables" value={`${data?.published_timetables ?? 0}/${data?.timetables ?? 0}`} hint="published / total" icon={<CalendarRange className="size-4" />} delay={0.28} />
      </div>

      <div className="grid lg:grid-cols-2 gap-4">
        <div className="glass rounded-xl p-5">
          <div className="flex items-baseline justify-between">
            <h3 className="font-semibold">Lecturer Workload</h3>
            <span className="text-xs text-muted-foreground">% utilization vs cap</span>
          </div>
          <div className="h-72 mt-4">
            <ResponsiveContainer>
              <BarChart data={(workload.data ?? []).slice(0, 12)}>
                <XAxis dataKey="name" tick={{ fontSize: 11 }} stroke="var(--muted-foreground)" />
                <YAxis tick={{ fontSize: 11 }} stroke="var(--muted-foreground)" />
                <Tooltip contentStyle={{ background: "var(--popover)", border: "1px solid var(--border)", borderRadius: 8, fontSize: 12 }} />
                <Bar dataKey="utilization" radius={[6, 6, 0, 0]}>
                  {(workload.data ?? []).map((row, i) => (
                    <Cell key={i} fill={row.overloaded ? "var(--destructive)" : "var(--primary)"} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="glass rounded-xl p-5">
          <div className="flex items-baseline justify-between">
            <h3 className="font-semibold">Room Utilization</h3>
            <span className="text-xs text-muted-foreground">% of weekly slots used</span>
          </div>
          <div className="h-72 mt-4">
            <ResponsiveContainer>
              <BarChart data={(rooms.data ?? []).slice(0, 12)}>
                <XAxis dataKey="code" tick={{ fontSize: 11 }} stroke="var(--muted-foreground)" />
                <YAxis tick={{ fontSize: 11 }} stroke="var(--muted-foreground)" />
                <Tooltip contentStyle={{ background: "var(--popover)", border: "1px solid var(--border)", borderRadius: 8, fontSize: 12 }} />
                <Bar dataKey="utilization" radius={[6, 6, 0, 0]} fill="var(--chart-2)" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {isLoading && <div className="text-sm text-muted-foreground">Loading dashboard…</div>}
    </div>
  );
}
