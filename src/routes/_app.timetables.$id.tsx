import { createFileRoute, Link } from "@tanstack/react-router";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { motion } from "framer-motion";
import { ArrowLeft, CheckCircle2, Download, FileText, Send } from "lucide-react";
import { api } from "@/lib/api";
import { PageHeader } from "@/components/app/page-header";
import { Button } from "@/components/ui/button";
import { toast } from "sonner";

export const Route = createFileRoute("/_app/timetables/$id")({ component: Page });

const DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];

function Page() {
  const { id } = Route.useParams();
  const qc = useQueryClient();

  const tt = useQuery({
    queryKey: ["timetable", id],
    queryFn: async () => (await api.get(`/timetables/${id}`)).data,
  });
  const slots = useQuery({
    queryKey: ["time-slots-active"],
    queryFn: async () => {
      const r = (await api.get("/time-slots", { params: { page_size: 50 } })).data;
      const arr = Array.isArray(r) ? r : r.results;
      return arr.filter((s: any) => !s.is_lunch).sort((a: any, b: any) => a.order - b.order);
    },
  });

  const action = (kind: "submit_for_approval" | "hod_approve" | "dean_approve" | "publish") =>
    useMutation({
      mutationFn: async () => (await api.post(`/timetables/${id}/${kind}/`)).data,
      onSuccess: () => { toast.success("Updated"); qc.invalidateQueries({ queryKey: ["timetable", id] }); },
      onError: () => toast.error("Action failed"),
    });

  const submit = action("submit_for_approval");
  const hod = action("hod_approve");
  const dean = action("dean_approve");
  const publish = action("publish");

  if (tt.isLoading) return <div className="text-sm text-muted-foreground">Loading…</div>;
  if (!tt.data) return <div className="text-sm">Not found.</div>;

  const data = tt.data;
  const entries: any[] = data.entries ?? [];

  // build grid: day x slot -> entries
  const cell = (day: number, slotId: number) =>
    entries.filter((e) => e.day === day && e.time_slot === slotId);

  return (
    <div className="space-y-6">
      <PageHeader
        title={data.name}
        description={`Version ${data.version} · ${data.semester_name} · ${data.status}`}
        actions={
          <div className="flex gap-2">
            <Link to="/timetables"><Button variant="ghost"><ArrowLeft className="size-4" /> Back</Button></Link>
            <Button variant="secondary" onClick={() => submit.mutate()} disabled={submit.isPending}><Send className="size-4" /> Submit</Button>
            <Button variant="secondary" onClick={() => hod.mutate()} disabled={hod.isPending}><CheckCircle2 className="size-4" /> HOD</Button>
            <Button variant="secondary" onClick={() => dean.mutate()} disabled={dean.isPending}><CheckCircle2 className="size-4" /> Dean</Button>
            <Button onClick={() => publish.mutate()} disabled={publish.isPending}><FileText className="size-4" /> Publish</Button>
          </div>
        }
      />

      <div className="grid grid-cols-3 gap-3">
        <div className="glass rounded-xl p-4">
          <div className="text-xs text-muted-foreground">Score</div>
          <div className="text-2xl font-semibold mt-1">{data.optimization_score?.toFixed?.(1) ?? "—"}</div>
        </div>
        <div className="glass rounded-xl p-4">
          <div className="text-xs text-muted-foreground">Sessions</div>
          <div className="text-2xl font-semibold mt-1">{entries.length}</div>
        </div>
        <div className="glass rounded-xl p-4">
          <div className="text-xs text-muted-foreground">Violations</div>
          <div className="text-2xl font-semibold mt-1">
            <span className="text-destructive">{data.hard_violations}</span>
            <span className="text-muted-foreground text-base"> / </span>
            <span className="text-warning">{data.soft_violations}</span>
          </div>
        </div>
      </div>

      <div className="glass rounded-xl overflow-x-auto">
        <table className="w-full text-xs min-w-[800px]">
          <thead>
            <tr className="border-b border-border/60">
              <th className="px-3 py-3 text-left font-medium text-muted-foreground w-24">Time</th>
              {DAYS.map((d) => (
                <th key={d} className="px-3 py-3 text-left font-medium text-muted-foreground">{d}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {(slots.data ?? []).map((s: any) => (
              <tr key={s.id} className="border-b border-border/40 last:border-0 align-top">
                <td className="px-3 py-3 text-muted-foreground">
                  <div className="font-medium text-foreground">{s.name}</div>
                  <div>{s.start_time?.slice(0, 5)}–{s.end_time?.slice(0, 5)}</div>
                </td>
                {DAYS.map((_, day) => {
                  const items = cell(day, s.id);
                  return (
                    <td key={day} className="px-2 py-2 align-top">
                      <div className="space-y-1.5">
                        {items.map((e: any) => (
                          <motion.div
                            key={e.id}
                            initial={{ opacity: 0, scale: 0.96 }} animate={{ opacity: 1, scale: 1 }}
                            className="rounded-md border border-primary/30 bg-primary/10 p-2"
                          >
                            <div className="font-medium">{e.course_code}</div>
                            <div className="text-muted-foreground truncate">{e.course_title}</div>
                            <div className="text-[10px] text-muted-foreground mt-1">
                              {e.lecturer_name} · {e.room_code}
                            </div>
                          </motion.div>
                        ))}
                      </div>
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
