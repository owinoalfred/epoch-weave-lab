import { createFileRoute } from "@tanstack/react-router";
import { PageHeader } from "@/components/app/page-header";
import { ResourceTable } from "@/components/app/resource-table";
import { useOptions } from "@/lib/use-options";

export const Route = createFileRoute("/_app/semesters")({ component: Page });

function Page() {
  const years = useOptions<{ id: number; name: string }>("/academic-years", (y) => y.name);
  return (
    <div className="space-y-6">
      <PageHeader title="Semesters" description="Semester instances within each academic year." />
      <ResourceTable
        endpoint="/semesters"
        columns={[
          { key: "name", label: "Name" },
          { key: "number", label: "#" },
          { key: "start_date", label: "Start" },
          { key: "end_date", label: "End" },
          { key: "is_active", label: "Active", render: (r: any) => r.is_active ? "✓" : "—" },
        ]}
        fields={[
          { name: "academic_year", label: "Academic year", type: "select", required: true, options: years },
          { name: "name", label: "Name", required: true, placeholder: "Semester 1" },
          { name: "number", label: "Number", type: "number", required: true },
          { name: "start_date", label: "Start date", placeholder: "YYYY-MM-DD" },
          { name: "end_date", label: "End date", placeholder: "YYYY-MM-DD" },
          { name: "is_active", label: "Active", type: "checkbox" },
        ]}
      />
    </div>
  );
}
