import { createFileRoute } from "@tanstack/react-router";
import { PageHeader } from "@/components/app/page-header";
import { ResourceTable } from "@/components/app/resource-table";
import { useOptions } from "@/lib/use-options";

export const Route = createFileRoute("/_app/programmes")({ component: Page });

function Page() {
  const depts = useOptions<{ id: number; name: string; code: string }>("/departments", (d) => `${d.code} — ${d.name}`);
  return (
    <div className="space-y-6">
      <PageHeader title="Programmes" description="Degree programmes offered by each department." />
      <ResourceTable
        endpoint="/programmes"
        columns={[
          { key: "code", label: "Code" },
          { key: "name", label: "Name" },
          { key: "level", label: "Level" },
          { key: "duration_years", label: "Years" },
          { key: "department_name", label: "Department" },
        ]}
        fields={[
          { name: "department", label: "Department", type: "select", options: depts, required: true },
          { name: "code", label: "Code", required: true, placeholder: "BSCCS" },
          { name: "name", label: "Name", required: true },
          { name: "level", label: "Level", type: "select", required: true, options: [
            { value: "UG", label: "Undergraduate" },
            { value: "MS", label: "Masters" },
            { value: "PHD", label: "PhD" },
            { value: "PG", label: "Postgraduate" },
          ]},
          { name: "duration_years", label: "Duration (years)", type: "number" },
        ]}
      />
    </div>
  );
}
