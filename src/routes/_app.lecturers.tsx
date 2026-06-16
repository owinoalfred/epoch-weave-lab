import { createFileRoute } from "@tanstack/react-router";
import { PageHeader } from "@/components/app/page-header";
import { ResourceTable } from "@/components/app/resource-table";
import { useOptions } from "@/lib/use-options";

export const Route = createFileRoute("/_app/lecturers")({ component: Page });

function Page() {
  const depts = useOptions<{ id: number; name: string; code: string }>("/departments", (d) => `${d.code} — ${d.name}`);
  return (
    <div className="space-y-6">
      <PageHeader title="Lecturers" description="Teaching staff and workload caps by rank." />
      <ResourceTable
        endpoint="/lecturers"
        columns={[
          { key: "staff_no", label: "Staff #" },
          { key: "name", label: "Name" },
          { key: "rank", label: "Rank" },
          { key: "department_name", label: "Department" },
          { key: "max_weekly_hours", label: "Max hrs/wk" },
        ]}
        fields={[
          { name: "staff_no", label: "Staff number", required: true },
          { name: "user", label: "User ID", type: "number", required: true,
            placeholder: "Existing User PK (create via /api/auth/register)" },
          { name: "department", label: "Department", type: "select", required: true, options: depts },
          { name: "title", label: "Title", placeholder: "Dr." },
          { name: "rank", label: "Rank", type: "select", required: true, options: [
            { value: "LECTURER", label: "Lecturer (max 22 hrs)" },
            { value: "HOD", label: "Head of Department (max 16 hrs)" },
            { value: "DEAN", label: "Dean (max 12 hrs)" },
            { value: "LAB_ASSISTANT", label: "Lab Assistant (max 12 hrs)" },
          ]},
        ]}
      />
    </div>
  );
}
