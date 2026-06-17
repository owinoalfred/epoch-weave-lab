import { createFileRoute, Link } from "@tanstack/react-router";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { ArrowLeft, Send } from "lucide-react";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { toast } from "sonner";

export const Route = createFileRoute("/_app/timetables/$id")({ 
  component: Page 
});

const DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];

function Page() {
  const { id } = Route.useParams();
  const qc = useQueryClient();

  const tt = useQuery({
    queryKey: ["timetable", id],
    queryFn: async () => (await api.get(`/timetables/${id}/`)).data,
  });

  const slots = useQuery({
    queryKey: ["time-slots-active"],
    queryFn: async () => {
      const r = (await api.get("/time-slots/", { params: { page_size: 50 } })).data;
      const arr = Array.isArray(r) ? r : r.results;
      return arr.filter((s: any) => !s.is_lunch).sort((a: any, b: any) => a.order - b.order);
    },
  });

  const generateMutation = useMutation({
    mutationFn: async () => (await api.post(`/timetables/${id}/generate/`)).data,
    onSuccess: () => { 
      toast.success("Generation started!"); 
      qc.invalidateQueries({ queryKey: ["timetable", id] }); 
    },
    onError: () => toast.error("Failed to start generation"),
  });

  const publishMutation = useMutation({
    mutationFn: async () => (await api.post(`/timetables/${id}/publish/`)).data,
    onSuccess: () => { 
      toast.success("Timetable published!"); 
      qc.invalidateQueries({ queryKey: ["timetable", id] }); 
    },
    onError: () => toast.error("Failed to publish"),
  });

  if (tt.isLoading) return <div className="p-8">Loading…</div>;
  if (!tt.data) return <div className="p-8">Not found.</div>;

  const data = tt.data;
  const entries: any[] = data.entries ?? [];

  const cell = (day: number, slotId: number) =>
    entries.filter((e) => e.day === day && e.time_slot === slotId);

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Link to="/timetables">
            <Button variant="outline" size="icon"><ArrowLeft className="h-4 w-4" /></Button>
          </Link>
          <div>
            <h1 className="text-2xl font-bold">{data.name}</h1>
            <p className="text-gray-500">Version {data.version} • Status: {data.status}</p>
          </div>
        </div>

        <div className="flex gap-2">
          {data.status === "DRAFT" && (
            <Button 
              onClick={() => generateMutation.mutate()} 
              disabled={generateMutation.isPending}
            >
              <Send className="mr-2 h-4 w-4" /> Generate
            </Button>
          )}
          
          {data.status === "GENERATING" && (
            <Button disabled>Generating...</Button>
          )}

          {entries.length > 0 && data.status !== "PUBLISHED" && (
            <Button 
              variant="secondary"
              onClick={() => publishMutation.mutate()} 
              disabled={publishMutation.isPending}
            >
              Publish
            </Button>
          )}
        </div>
      </div>

      <div className="grid grid-cols-3 gap-4 max-w-2xl">
        <div className="bg-white p-4 rounded-lg shadow-sm border">
          <p className="text-sm text-gray-500">Score</p>
          <p className="text-2xl font-bold">{data.optimization_score?.toFixed?.(1) ?? "—"}</p>
        </div>
        <div className="bg-white p-4 rounded-lg shadow-sm border">
          <p className="text-sm text-gray-500">Sessions</p>
          <p className="text-2xl font-bold">{entries.length}</p>
        </div>
        <div className="bg-white p-4 rounded-lg shadow-sm border">
          <p className="text-sm text-gray-500">Violations</p>
          <p className="text-2xl font-bold">{data.hard_violations} / {data.soft_violations}</p>
        </div>
      </div>

      <div className="bg-white rounded-lg shadow-sm border overflow-x-auto">
        <table className="w-full text-sm text-left">
          <thead className="bg-gray-50 text-gray-600 uppercase text-xs">
            <tr>
              <th className="px-4 py-3">Time</th>
              {DAYS.map((d) => (
                <th key={d} className="px-4 py-3">{d}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {(slots.data ?? []).map((s: any) => (
              <tr key={s.id} className="border-t">
                <td className="px-4 py-3 font-medium whitespace-nowrap">
                  {s.name}<br/>
                  <span className="text-gray-500 text-xs">
                    {s.start_time?.slice(0, 5)}–{s.end_time?.slice(0, 5)}
                  </span>
                </td>
                {DAYS.map((_, day) => {
                  const items = cell(day, s.id);
                  return (
                    <td key={day} className="px-4 py-3 align-top">
                      {items.map((e: any) => (
                        <div key={e.id} className="bg-blue-50 p-2 rounded mb-2 border border-blue-100">
                          <div className="font-bold text-blue-900">{e.course_code}</div>
                          <div className="text-xs text-gray-600">{e.course_title}</div>
                          <div className="text-xs text-gray-500 mt-1">
                            {e.lecturer_name} • {e.room_code}
                          </div>
                        </div>
                      ))}
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