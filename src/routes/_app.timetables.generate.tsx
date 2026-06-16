import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useMutation } from "@tanstack/react-query";
import { Loader2, Sparkles, Wand2, ShieldCheck, Cpu } from "lucide-react";
import { api } from "@/lib/api";
import { PageHeader } from "@/components/app/page-header";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useOptions } from "@/lib/use-options";
import { toast } from "sonner";

export const Route = createFileRoute("/_app/timetables/generate")({ component: Page });

function Page() {
  const navigate = useNavigate();
  const semesters = useOptions<{ id: number; name: string; academic_year: number }>(
    "/semesters", (s: any) => `${s.academic_year} · ${s.name}`);
  const [progress, setProgress] = useState<string | null>(null);

  const generate = useMutation({
    mutationFn: async (payload: any) => (await api.post("/timetable/generate", payload)).data,
    onMutate: () => setProgress("Submitting solver job…"),
    onSuccess: (data) => {
      if (data.timetable_id) {
        toast.success("Timetable generated");
        navigate({ to: "/timetables/$id", params: { id: String(data.timetable_id) } });
      } else if (data.task_id) {
        toast.message("Solver queued", { description: `Task ${data.task_id}` });
        setProgress(`Queued. Task ${data.task_id}. Check Timetables list shortly.`);
      }
    },
    onError: (e: any) => {
      setProgress(null);
      toast.error(e?.response?.data ? JSON.stringify(e.response.data) : "Generation failed");
    },
  });

  const onSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const fd = new FormData(e.currentTarget);
    generate.mutate({
      semester_id: Number(fd.get("semester_id")),
      name: String(fd.get("name")),
      time_limit_seconds: Number(fd.get("time_limit_seconds") || 30),
      sync: fd.get("sync") === "on",
    });
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Generate Timetable"
        description="Run the OR-Tools CP-SAT solver across all course allocations for a semester."
      />

      <div className="grid lg:grid-cols-3 gap-4">
        <form onSubmit={onSubmit} className="glass rounded-xl p-6 space-y-4 lg:col-span-2">
          <div className="space-y-1.5">
            <Label htmlFor="semester_id">Semester</Label>
            <select id="semester_id" name="semester_id" required
              className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm">
              <option value="">Select a semester…</option>
              {semesters.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
            </select>
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="name">Timetable name</Label>
            <Input id="name" name="name" required defaultValue="Auto-generated draft" />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1.5">
              <Label htmlFor="time_limit_seconds">Solver time limit (s)</Label>
              <Input id="time_limit_seconds" name="time_limit_seconds" type="number" defaultValue={30} min={5} max={600} />
            </div>
            <label className="flex items-center gap-2 self-end pb-2 text-sm text-muted-foreground">
              <input type="checkbox" name="sync" className="size-4" defaultChecked />
              Run synchronously
            </label>
          </div>

          <Button type="submit" className="w-full" disabled={generate.isPending}>
            {generate.isPending ? <Loader2 className="size-4 animate-spin" /> : <Sparkles className="size-4" />}
            Generate Timetable
          </Button>

          <AnimatePresence>
            {progress && (
              <motion.div
                initial={{ opacity: 0, y: 4 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}
                className="text-xs text-muted-foreground bg-card/40 border border-border/60 rounded-md p-3"
              >{progress}</motion.div>
            )}
          </AnimatePresence>
        </form>

        <div className="space-y-3">
          <div className="glass rounded-xl p-5">
            <div className="flex items-center gap-2 font-semibold"><Cpu className="size-4 text-primary" /> Engine</div>
            <p className="text-xs text-muted-foreground mt-2">
              Google OR-Tools CP-SAT models the problem as a constraint satisfaction problem with
              decision variables for day, time-slot and room per session.
            </p>
          </div>
          <div className="glass rounded-xl p-5">
            <div className="flex items-center gap-2 font-semibold"><ShieldCheck className="size-4 text-success" /> Hard constraints</div>
            <ul className="text-xs text-muted-foreground mt-2 space-y-1 list-disc pl-4">
              <li>No lecturer / room / group / lab clashes</li>
              <li>Room capacity ≥ group size</li>
              <li>Equipment & room-type compatibility</li>
              <li>Lecturer max weekly hours by rank</li>
              <li>Group day caps (UG sem 1: 4, others: 3; PG: Saturday)</li>
            </ul>
          </div>
          <div className="glass rounded-xl p-5">
            <div className="flex items-center gap-2 font-semibold"><Wand2 className="size-4 text-warning" /> Soft objective</div>
            <ul className="text-xs text-muted-foreground mt-2 space-y-1 list-disc pl-4">
              <li>Minimize idle gaps</li>
              <li>Balance lecturer & student loads</li>
              <li>Maximize room utilization</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}
