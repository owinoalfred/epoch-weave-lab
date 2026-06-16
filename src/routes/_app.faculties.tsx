import { createFileRoute } from "@tanstack/react-router";
import { PageHeader } from "@/components/app/page-header";
import { ResourceTable } from "@/components/app/resource-table";

export const Route = createFileRoute("/_app/faculties")({ component: Page });

function Page() {
  return (
    <div className="space-y-6">
      <PageHeader title="Faculties" description="Top-level academic units of the university." />
      <ResourceTable
        endpoint="/faculties"
        columns={[
          { key: "code", label: "Code" },
          { key: "name", label: "Name" },
          { key: "departments_count", label: "Departments" },
        ]}
        fields={[
          { name: "code", label: "Code", required: true, placeholder: "FOC" },
          { name: "name", label: "Name", required: true, placeholder: "Faculty of Computing" },
        ]}
      />
    </div>
  );
}
