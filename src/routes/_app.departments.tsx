import { createFileRoute } from "@tanstack/react-router";
import { PageHeader } from "@/components/app/page-header";
import { ResourceTable } from "@/components/app/resource-table";
import { useOptions } from "@/lib/use-options";

export const Route = createFileRoute("/_app/departments")({ component: Page });

function Page() {
  const faculties = useOptions<{ id: number; name: string; code: string }>("/faculties", (f) => `${f.code} — ${f.name}`);
  return (
    <div className="space-y-6">
      <PageHeader title="Departments" description="Departments within each faculty." />
      <ResourceTable
        endpoint="/departments"
        columns={[
          { key: "code", label: "Code" },
          { key: "name", label: "Name" },
          { key: "faculty_name", label: "Faculty" },
          { key: "programmes_count", label: "Programmes" },
        ]}
        fields={[
          { name: "faculty", label: "Faculty", type: "select", options: faculties, required: true },
          { name: "code", label: "Code", required: true },
          { name: "name", label: "Name", required: true },
        ]}
      />
    </div>
  );
}
