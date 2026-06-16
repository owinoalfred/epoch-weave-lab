import { createFileRoute, Link } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { motion } from "framer-motion";
import { Eye, Sparkles, CheckCircle2, Clock, AlertTriangle } from "lucide-react";
import { api } from "@/lib/api";
import { PageHeader } from "@/components/app/page-header";
import { Button } from "@/components/ui/button";

export const Route = createFileRoute("/_app/timetables/")({ component: Page });

const statusBadge: Record<string, string> = {
  DRAFT: "bg-muted text-muted-foreground",
  GENERATING: "bg-warning/20 text-warning",
  READY: "bg-primary/20 text-primary",
  HOD_APPROVED: "bg-primary/20 text-primary",
  DEAN_APPROVED: "bg-primary/20 text-primary",
  PUBLISHED: "bg-success/20 text-success",
  ARCHIVED: "bg-muted text-muted-foreground",
};

function Page() {
  const { data, isLoading } = useQuery({
    queryKey: ["timetables"],
    queryFn: async () => (await api.get("/timetables")).data.results ?? (await api.get("/timetables")).data,
  });

  return (
    <div className="space-y-6">
      <PageHeader
        title="Timetables"
        description="Drafts, approved versions and published schedules."
        actions={
          <Link to="/timetables/generate">
            <Button><Sparkles className="size-4" /> Generate</Button>
          </Link>
        }
      />

      <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-3">
        {isLoading && <div className="text-sm text-muted-foreground">Loading…</div>}
        {data?.length === 0 && (
          <div className="glass rounded-xl p-10 text-center col-span-full">
            <div className="text-muted-foreground">No timetables yet.</div>
            <Link to="/timetables/generate" className="inline-block mt-3">
              <Button><Sparkles className="size-4" /> Generate your first timetable</Button>
            </Link>
          </div>
        )}
        {data?.map((t: any, i: number) => (
          <motion.div
            key={t.id}
            initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.04 }}
            className="glass rounded-xl p-5 flex flex-col gap-3"
          >
            <div className="flex items-start justify-between gap-3">
              <div className="min-w-0">
                <div className="font-semibold truncate">{t.name}</div>
                <div className="text-xs text-muted-foreground">v{t.version} · {t.semester_name}</div>
              </div>
              <span className={`text-[10px] uppercase tracking-wider rounded-full px-2 py-0.5 ${statusBadge[t.status] ?? ""}`}>
                {t.status}
              </span>
            </div>
            <div className="flex items-center gap-4 text-xs text-muted-foreground">
              <span className="flex items-center gap-1"><Clock className="size-3.5" />{t.entry_count} sessions</span>
              {t.optimization_score != null && (
                <span className="flex items-center gap-1"><CheckCircle2 className="size-3.5 text-success" />score {Math.round(t.optimization_score)}</span>
              )}
              {t.hard_violations > 0 && (
                <span className="flex items-center gap-1 text-destructive"><AlertTriangle className="size-3.5" />{t.hard_violations} hard</span>
              )}
            </div>
            <Link to="/timetables/$id" params={{ id: String(t.id) }} className="mt-auto">
              <Button variant="secondary" className="w-full"><Eye className="size-4" /> View</Button>
            </Link>
          </motion.div>
        ))}
      </div>
    </div>
  );
}
