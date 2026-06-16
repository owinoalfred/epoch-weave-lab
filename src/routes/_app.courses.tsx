import { createFileRoute } from "@tanstack/react-router";
import { PageHeader } from "@/components/app/page-header";
import { ResourceTable } from "@/components/app/resource-table";
import { useOptions } from "@/lib/use-options";

export const Route = createFileRoute("/_app/courses")({ component: Page });

function Page() {
  const progs = useOptions<{ id: number; name: string; code: string }>("/programmes", (p) => `${p.code} — ${p.name}`);
  return (
    <div className="space-y-6">
      <PageHeader title="Courses" description="Course units offered per programme." />
      <ResourceTable
        endpoint="/courses"
        columns={[
          { key: "code", label: "Code" },
          { key: "title", label: "Title" },
          { key: "programme_code", label: "Programme" },
          { key: "credit_units", label: "CU" },
          { key: "weekly_hours", label: "Hrs/wk" },
          { key: "has_lab", label: "Lab", render: (r: any) => r.has_lab ? "Yes" : "—" },
        ]}
        fields={[
          { name: "programme", label: "Programme", type: "select", required: true, options: progs },
          { name: "code", label: "Code", required: true, placeholder: "CS101" },
          { name: "title", label: "Title", required: true },
          { name: "credit_units", label: "Credit units", type: "number" },
          { name: "weekly_hours", label: "Weekly hours", type: "number" },
          { name: "year_of_study", label: "Year of study", type: "number" },
          { name: "semester_number", label: "Semester (1/2)", type: "number" },
          { name: "has_lab", label: "Has lab session", type: "checkbox" },
        ]}
      />
    </div>
  );
}
