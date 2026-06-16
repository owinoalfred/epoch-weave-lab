import { Link, useRouterState } from "@tanstack/react-router";
import { motion } from "framer-motion";
import {
  LayoutDashboard, Building2, GitBranch, GraduationCap,
  BookOpen, Users, DoorOpen, UsersRound, CalendarRange,
  Sparkles, BarChart3, Settings, LogOut, CalendarDays,
} from "lucide-react";
import { useAuth } from "@/lib/auth-store";
import { cn } from "@/lib/utils";

const nav = [
  { to: "/", label: "Dashboard", icon: LayoutDashboard },
  { section: "Academics" },
  { to: "/faculties", label: "Faculties", icon: Building2 },
  { to: "/departments", label: "Departments", icon: GitBranch },
  { to: "/programmes", label: "Programmes", icon: GraduationCap },
  { to: "/courses", label: "Courses", icon: BookOpen },
  { to: "/semesters", label: "Semesters", icon: CalendarDays },
  { section: "People & Spaces" },
  { to: "/lecturers", label: "Lecturers", icon: Users },
  { to: "/rooms", label: "Rooms", icon: DoorOpen },
  { to: "/student-groups", label: "Student Groups", icon: UsersRound },
  { section: "Timetables" },
  { to: "/timetables", label: "Timetables", icon: CalendarRange },
  { to: "/timetables/generate", label: "Generate", icon: Sparkles },
  { to: "/analytics", label: "Analytics", icon: BarChart3 },
  { section: "System" },
  { to: "/settings", label: "Settings", icon: Settings },
] as const;

export function Sidebar() {
  const pathname = useRouterState({ select: (s) => s.location.pathname });
  const { user, logout } = useAuth();

  return (
    <aside className="hidden md:flex w-64 shrink-0 flex-col border-r border-sidebar-border bg-sidebar text-sidebar-foreground">
      <div className="flex h-14 items-center gap-2 px-5 border-b border-sidebar-border">
        <div className="size-7 rounded-md bg-primary/90 grid place-items-center text-primary-foreground font-bold shadow-glow">U</div>
        <div className="font-semibold tracking-tight">UniTime</div>
        <span className="ml-auto text-[10px] uppercase text-muted-foreground tracking-wider">v1</span>
      </div>
      <nav className="flex-1 overflow-y-auto px-2 py-3 space-y-0.5">
        {nav.map((item, i) =>
          "section" in item ? (
            <div key={i} className="px-3 pt-4 pb-1 text-[10px] font-medium uppercase tracking-wider text-muted-foreground">
              {item.section}
            </div>
          ) : (
            <Link
              key={item.to}
              to={item.to}
              className={cn(
                "group flex items-center gap-2.5 rounded-md px-3 py-2 text-sm transition-colors",
                pathname === item.to
                  ? "bg-sidebar-accent text-sidebar-accent-foreground"
                  : "text-muted-foreground hover:bg-sidebar-accent/60 hover:text-sidebar-foreground"
              )}
            >
              <item.icon className="size-4" />
              <span>{item.label}</span>
              {pathname === item.to && (
                <motion.div layoutId="nav-dot" className="ml-auto size-1.5 rounded-full bg-primary" />
              )}
            </Link>
          )
        )}
      </nav>
      <div className="border-t border-sidebar-border p-3">
        <div className="flex items-center gap-2 rounded-md px-2 py-2">
          <div className="size-8 rounded-full bg-accent grid place-items-center text-xs font-medium">
            {(user?.first_name?.[0] ?? user?.username?.[0] ?? "?").toUpperCase()}
          </div>
          <div className="min-w-0 flex-1">
            <div className="truncate text-sm font-medium">{user?.first_name || user?.username || "Guest"}</div>
            <div className="truncate text-xs text-muted-foreground">{user?.roles?.[0] ?? "—"}</div>
          </div>
          <button onClick={logout} className="rounded-md p-1.5 hover:bg-accent text-muted-foreground hover:text-foreground transition-colors" aria-label="Sign out">
            <LogOut className="size-4" />
          </button>
        </div>
      </div>
    </aside>
  );
}
