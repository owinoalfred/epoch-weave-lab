import { createFileRoute, useNavigate, Link } from "@tanstack/react-router";
import { useState } from "react";
import { Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useAuth } from "@/lib/auth-store";
import { toast } from "sonner";

export const Route = createFileRoute("/register")({
  component: RegisterPage,
});

function RegisterPage() {
  const navigate = useNavigate();
  const register = useAuth((s) => s.register);
  const [loading, setLoading] = useState(false);

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const fd = new FormData(e.currentTarget);
    
    const payload = {
      username: String(fd.get("username")),
      email: String(fd.get("email")),
      password: String(fd.get("password")),
      first_name: String(fd.get("first_name")),
      last_name: String(fd.get("last_name")),
    };

    setLoading(true);
    try {
      await register(payload);
      toast.success("Account created successfully!");
      navigate({ to: "/" });
    } catch (err: any) {
      const errors = err?.response?.data;
      if (errors) {
        const firstError = Object.values(errors).flat()[0];
        toast.error(String(firstError));
      } else {
        toast.error("Registration failed");
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 p-4">
      <div className="w-full max-w-md space-y-8 bg-white p-8 rounded-xl shadow-lg">
        <div className="text-center">
          <h1 className="text-3xl font-bold text-gray-900">Create Account</h1>
          <p className="mt-2 text-gray-600">Join UniTime to manage timetables</p>
        </div>

        <form className="mt-8 space-y-6" onSubmit={onSubmit}>
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="first_name">First Name</Label>
                <Input id="first_name" name="first_name" type="text" required className="mt-1" />
              </div>
              <div>
                <Label htmlFor="last_name">Last Name</Label>
                <Input id="last_name" name="last_name" type="text" required className="mt-1" />
              </div>
            </div>
            
            <div>
              <Label htmlFor="username">Username</Label>
              <Input id="username" name="username" type="text" required className="mt-1" />
            </div>

            <div>
              <Label htmlFor="email">Email Address</Label>
              <Input id="email" name="email" type="email" required className="mt-1" />
            </div>

            <div>
              <Label htmlFor="password">Password</Label>
              <Input id="password" name="password" type="password" minLength={8} required className="mt-1" />
              <p className="text-xs text-gray-500 mt-1">Must be at least 8 characters.</p>
            </div>
          </div>

          <Button type="submit" className="w-full" disabled={loading}>
            {loading ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : null}
            Create Account
          </Button>
        </form>

        <div className="text-center text-sm">
          <span className="text-gray-600">Already have an account? </span>
          <Link to="/login" className="font-medium text-blue-600 hover:text-blue-500">
            Sign in
          </Link>
        </div>
      </div>
    </div>
  );
}