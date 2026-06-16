import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { motion, AnimatePresence } from "framer-motion";
import { Plus, Trash2, Pencil, X, Loader2 } from "lucide-react";
import { api, type Paginated } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { toast } from "sonner";

export interface FieldDef {
  name: string;
  label: string;
  type?: "text" | "number" | "select" | "checkbox";
  required?: boolean;
  options?: { value: string | number; label: string }[];
  placeholder?: string;
}

interface Props<T extends { id: number }> {
  endpoint: string; // e.g. "/faculties"
  columns: { key: keyof T | string; label: string; render?: (row: T) => React.ReactNode }[];
  fields: FieldDef[];
  emptyHint?: string;
}

export function ResourceTable<T extends { id: number }>({ endpoint, columns, fields, emptyHint }: Props<T>) {
  const qc = useQueryClient();
  const [openForm, setOpenForm] = useState(false);
  const [editing, setEditing] = useState<T | null>(null);
  const [search, setSearch] = useState("");

  const list = useQuery({
    queryKey: [endpoint, search],
    queryFn: async () => {
      const { data } = await api.get<Paginated<T> | T[]>(endpoint, { params: { search } });
      return Array.isArray(data) ? data : data.results;
    },
  });

  const save = useMutation({
    mutationFn: async (payload: Partial<T>) => {
      if (editing) {
        const { data } = await api.patch(`${endpoint}/${editing.id}/`, payload);
        return data;
      }
      const { data } = await api.post(`${endpoint}/`, payload);
      return data;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: [endpoint] });
      toast.success(editing ? "Updated" : "Created");
      setOpenForm(false);
      setEditing(null);
    },
    onError: (e: any) => toast.error(e?.response?.data ? JSON.stringify(e.response.data) : "Failed"),
  });

  const remove = useMutation({
    mutationFn: async (id: number) => api.delete(`${endpoint}/${id}/`),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: [endpoint] });
      toast.success("Deleted");
    },
    onError: () => toast.error("Delete failed"),
  });

  const onSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const fd = new FormData(e.currentTarget);
    const payload: Record<string, any> = {};
    fields.forEach((f) => {
      const raw = fd.get(f.name);
      if (raw === null) return;
      if (f.type === "number") payload[f.name] = raw === "" ? null : Number(raw);
      else if (f.type === "checkbox") payload[f.name] = raw === "on";
      else payload[f.name] = raw;
    });
    save.mutate(payload as Partial<T>);
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2">
        <Input
          placeholder="Search…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="max-w-xs"
        />
        <Button
          className="ml-auto"
          onClick={() => { setEditing(null); setOpenForm(true); }}
        >
          <Plus className="size-4" /> New
        </Button>
      </div>

      <div className="glass rounded-xl overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-border/60 text-left text-xs uppercase tracking-wider text-muted-foreground">
              {columns.map((c) => (
                <th key={String(c.key)} className="px-4 py-3 font-medium">{c.label}</th>
              ))}
              <th className="px-4 py-3 w-24"></th>
            </tr>
          </thead>
          <tbody>
            {list.isLoading && (
              <tr><td colSpan={columns.length + 1} className="px-4 py-10 text-center text-muted-foreground">
                <Loader2 className="size-4 animate-spin inline mr-2" /> Loading…
              </td></tr>
            )}
            {!list.isLoading && list.data?.length === 0 && (
              <tr><td colSpan={columns.length + 1} className="px-4 py-12 text-center text-muted-foreground">
                {emptyHint ?? "No records yet."}
              </td></tr>
            )}
            {list.data?.map((row) => (
              <tr key={row.id} className="border-b border-border/40 last:border-0 hover:bg-accent/30 transition-colors">
                {columns.map((c) => (
                  <td key={String(c.key)} className="px-4 py-3">
                    {c.render ? c.render(row) : String((row as any)[c.key] ?? "—")}
                  </td>
                ))}
                <td className="px-4 py-3 text-right">
                  <button onClick={() => { setEditing(row); setOpenForm(true); }} className="rounded-md p-1.5 hover:bg-accent text-muted-foreground hover:text-foreground" aria-label="Edit">
                    <Pencil className="size-4" />
                  </button>
                  <button onClick={() => { if (confirm("Delete this record?")) remove.mutate(row.id); }} className="rounded-md p-1.5 hover:bg-accent text-muted-foreground hover:text-destructive" aria-label="Delete">
                    <Trash2 className="size-4" />
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <AnimatePresence>
        {openForm && (
          <motion.div
            initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 bg-background/70 backdrop-blur-sm flex items-center justify-center p-4"
            onClick={() => setOpenForm(false)}
          >
            <motion.form
              initial={{ scale: 0.96, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} exit={{ scale: 0.96, opacity: 0 }}
              onClick={(e) => e.stopPropagation()}
              onSubmit={onSubmit}
              className="glass w-full max-w-lg rounded-xl p-6 space-y-4 shadow-glow"
            >
              <div className="flex items-center justify-between">
                <h2 className="text-lg font-semibold">{editing ? "Edit" : "Create"}</h2>
                <button type="button" onClick={() => setOpenForm(false)} className="rounded-md p-1.5 hover:bg-accent"><X className="size-4" /></button>
              </div>
              <div className="space-y-3 max-h-[60vh] overflow-y-auto pr-1">
                {fields.map((f) => (
                  <div key={f.name} className="space-y-1.5">
                    <Label htmlFor={f.name}>{f.label}{f.required && <span className="text-destructive"> *</span>}</Label>
                    {f.type === "select" ? (
                      <select
                        id={f.name} name={f.name} required={f.required}
                        defaultValue={editing ? (editing as any)[f.name] ?? "" : ""}
                        className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                      >
                        <option value="">—</option>
                        {f.options?.map((o) => (
                          <option key={o.value} value={o.value}>{o.label}</option>
                        ))}
                      </select>
                    ) : f.type === "checkbox" ? (
                      <input id={f.name} name={f.name} type="checkbox"
                        defaultChecked={editing ? !!(editing as any)[f.name] : false}
                        className="size-4 rounded border-input" />
                    ) : (
                      <Input
                        id={f.name} name={f.name} type={f.type ?? "text"}
                        required={f.required} placeholder={f.placeholder}
                        defaultValue={editing ? (editing as any)[f.name] ?? "" : ""}
                      />
                    )}
                  </div>
                ))}
              </div>
              <div className="flex justify-end gap-2 pt-2 border-t border-border/60">
                <Button type="button" variant="ghost" onClick={() => setOpenForm(false)}>Cancel</Button>
                <Button type="submit" disabled={save.isPending}>
                  {save.isPending && <Loader2 className="size-4 animate-spin" />}
                  {editing ? "Save" : "Create"}
                </Button>
              </div>
            </motion.form>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
