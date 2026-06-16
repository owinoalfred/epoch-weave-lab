import { createFileRoute } from "@tanstack/react-router";
import { PageHeader } from "@/components/app/page-header";
import { ResourceTable } from "@/components/app/resource-table";

export const Route = createFileRoute("/_app/rooms")({ component: Page });

function Page() {
  return (
    <div className="space-y-6">
      <PageHeader title="Rooms" description="Lecture rooms, labs, computer labs and auditoriums." />
      <ResourceTable
        endpoint="/rooms"
        columns={[
          { key: "code", label: "Code" },
          { key: "name", label: "Name" },
          { key: "building", label: "Building" },
          { key: "capacity", label: "Capacity" },
          { key: "room_type", label: "Type" },
          { key: "is_active", label: "Active", render: (r: any) => r.is_active ? "✓" : "—" },
        ]}
        fields={[
          { name: "code", label: "Code", required: true, placeholder: "LR-101" },
          { name: "name", label: "Name", required: true },
          { name: "building", label: "Building", required: true },
          { name: "floor", label: "Floor" },
          { name: "capacity", label: "Capacity", type: "number", required: true },
          { name: "room_type", label: "Type", type: "select", required: true, options: [
            { value: "LECTURE", label: "Lecture Room" },
            { value: "LAB", label: "Laboratory" },
            { value: "COMPUTER_LAB", label: "Computer Lab" },
            { value: "SEMINAR", label: "Seminar Room" },
            { value: "AUDITORIUM", label: "Auditorium" },
          ]},
          { name: "is_active", label: "Active", type: "checkbox" },
        ]}
      />
    </div>
  );
}
