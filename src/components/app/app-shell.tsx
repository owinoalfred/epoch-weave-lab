import { useEffect } from "react";
import { Outlet, useNavigate, useRouterState } from "@tanstack/react-router";
import { Sidebar } from "./sidebar";
import { useAuth } from "@/lib/auth-store";

export function AppShell() {
  const { isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const pathname = useRouterState({ select: (s) => s.location.pathname });

  useEffect(() => {
    if (!isAuthenticated && pathname !== "/login") {
      navigate({ to: "/login" });
    }
  }, [isAuthenticated, pathname, navigate]);

  if (!isAuthenticated) return null;

  return (
    <div className="flex h-screen w-full bg-background text-foreground">
      <Sidebar />
      <main className="flex-1 overflow-y-auto">
        <div className="mx-auto w-full max-w-7xl px-6 py-6 space-y-6">
          <Outlet />
        </div>
      </main>
    </div>
  );
}
