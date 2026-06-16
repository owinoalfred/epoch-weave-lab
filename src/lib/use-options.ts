import { useQuery } from "@tanstack/react-query";
import { api, type Paginated } from "@/lib/api";

// fetch helper used by select options
export function useOptions<T extends { id: number }>(endpoint: string, label: (x: T) => string) {
  const q = useQuery({
    queryKey: ["options", endpoint],
    queryFn: async () => {
      const { data } = await api.get<Paginated<T> | T[]>(endpoint, { params: { page_size: 200 } });
      return Array.isArray(data) ? data : data.results;
    },
  });
  return (q.data ?? []).map((r) => ({ value: r.id, label: label(r) }));
}
