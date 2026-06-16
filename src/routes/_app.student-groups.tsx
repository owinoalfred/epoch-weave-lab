import { createFileRoute } from "@tanstack/react-router";
import { PageHeader } from "@/components/app/page-header";
import { ResourceTable } from "@/components/app/resource-table";
import { useOptions } from "@/lib/use-options";

export const Route = createFileRoute("/_app/student-groups")({ component: Page });

function Page() {
  const progs = useOptions<{ id: number; name: string; code: string }>("/programmes", (p) => `${p.code} — ${p.name}`);
  return (
    <div className="space-y-6">
      <PageHeader title="Student Groups" description="Cohorts that attend timetable sessions together." />
      <ResourceTable
        endpoint="/student-groups"
        columns={[
          { key: "name", label: "Name" },
          { key: "programme_code", label: "Programme" },
          { key: "year_of_study", label: "Year" },
          { key: "size", label: "Size" },
        ]}
        fields={[
          { name: "programme", label: "Programme", type: "select", required: true, options: progs },
          { name: "name", label: "Group name", required: true, placeholder: "Group A" },
          { name: "year_of_study", label: "Year of study", type: "number", required: true },
          { name: "size", label: "Group size", type: "number", required: true },
        ]}
      />
    </div>
  );
}
