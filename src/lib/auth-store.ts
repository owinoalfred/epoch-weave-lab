import { create } from "zustand";
import { persist } from "zustand/middleware";
import { api } from "./api";

export interface AuthUser {
  id: number;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  roles: string[];
}

interface AuthState {
  user: AuthUser | null;
  access: string | null;
  refresh: string | null;
  isAuthenticated: boolean;
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
  loadMe: () => Promise<void>;
}

export const useAuth = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      access: null,
      refresh: null,
      isAuthenticated: false,
      async login(username, password) {
        const { data } = await api.post("/auth/login", { username, password });
        localStorage.setItem("unitime_access", data.access);
        localStorage.setItem("unitime_refresh", data.refresh);
        set({ access: data.access, refresh: data.refresh, user: data.user, isAuthenticated: true });
      },
      logout() {
        localStorage.removeItem("unitime_access");
        localStorage.removeItem("unitime_refresh");
        set({ user: null, access: null, refresh: null, isAuthenticated: false });
      },
      async loadMe() {
        try {
          const { data } = await api.get("/auth/me");
          set({ user: data, isAuthenticated: true });
        } catch {
          get().logout();
        }
      },
    }),
    { name: "unitime-auth", partialize: (s) => ({ user: s.user, access: s.access, refresh: s.refresh, isAuthenticated: s.isAuthenticated }) }
  )
);
