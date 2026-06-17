import { createFileRoute, useNavigate, redirect } from "@tanstack/react-router";
import { useState } from "react";
import { motion } from "framer-motion";
import { Loader2, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useAuth } from "@/lib/auth-store";
import { toast } from "sonner";

export const Route = createFileRoute("/login")({
  component: LoginPage,
});

function LoginPage() {
  const navigate = useNavigate();
  const login = useAuth((s) => s.login);
  const [loading, setLoading] = useState(false);

  const onSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const fd = new FormData(e.currentTarget);
    setLoading(true);
    try {
      await login(String(fd.get("username")), String(fd.get("password")));
      toast.success("Welcome back");
      navigate({ to: "/" });
    } catch (err: any) {
      toast.error(err?.response?.data?.detail ?? "Invalid credentials");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen grid place-items-center grid-bg relative overflow-hidden">
      <div className="absolute inset-0 bg-gradient-to-br from-primary/10 via-transparent to-transparent pointer-events-none" />
      <motion.div
        initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.35 }}
        className="glass relative z-10 w-full max-w-md rounded-2xl p-8 shadow-glow"
      >
        <div className="flex items-center gap-2 mb-6">
          <div className="size-9 rounded-lg bg-primary grid place-items-center text-primary-foreground font-bold">U</div>
          <div>
            <div className="font-semibold tracking-tight">UniTime</div>
            <div className="text-xs text-muted-foreground">University Timetabling Platform</div>
          </div>
        </div>
        <h1 className="text-2xl font-semibold tracking-tight">Sign in</h1>
        <p className="text-sm text-muted-foreground mt-1">Use your university credentials to continue.</p>

        <form onSubmit={onSubmit} className="mt-6 space-y-4">
          <div className="space-y-1.5">
            <Label htmlFor="username">Username</Label>
            <Input id="username" name="username" required autoComplete="username" defaultValue="admin" />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="password">Password</Label>
            <Input id="password" name="password" type="password" required autoComplete="current-password" defaultValue="admin12345" />
          </div>
          <Button type="submit" className="w-full" disabled={loading}>
            {loading ? <Loader2 className="size-4 animate-spin" /> : <Sparkles className="size-4" />}
            Sign in
          </Button>
        </form>

        <div className="mt-6 rounded-lg border border-border/60 bg-card/40 p-3 text-xs text-muted-foreground space-y-1">
          <div className="font-medium text-foreground">Demo accounts</div>
          <div><code className="text-primary">admin / admin12345</code> — Super Admin</div>
          <div><code className="text-primary">dean / password123</code> · <code className="text-primary">hod / password123</code> · <code className="text-primary">officer / password123</code></div>
          <div className="pt-1 text-[10px]">Demo mode runs entirely in your browser. Set <code>VITE_API_URL</code> to connect the Django backend.</div>
        </div>
      </motion.div>
    </div>
  );
}
