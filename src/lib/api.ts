import axios from "axios";
import { mockAdapter } from "./mock/adapter";

/**
 * If VITE_API_URL is set we talk to the real Django backend; otherwise we
 * run a full in-browser mock backend (see ./mock/) so the UI is usable in
 * the Lovable preview without any server. To force-disable demo mode set
 * VITE_API_URL to your Django URL (e.g. http://localhost:8000/api).
 */
const configuredUrl = (import.meta.env.VITE_API_URL as string | undefined)?.trim();
export const DEMO_MODE = !configuredUrl;
const baseURL = configuredUrl || "http://demo.local/api";

export const api = axios.create({
  baseURL,
  withCredentials: false,
  adapter: DEMO_MODE ? mockAdapter : undefined,
});

api.interceptors.request.use((config) => {
  if (typeof window !== "undefined") {
    const token = localStorage.getItem("unitime_access");
    if (token) config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (r) => r,
  async (error) => {
    if (error.response?.status === 401 && typeof window !== "undefined" && !DEMO_MODE) {
      const refresh = localStorage.getItem("unitime_refresh");
      if (refresh && !error.config._retry) {
        try {
          const { data } = await axios.post(`${baseURL}/auth/refresh`, { refresh });
          localStorage.setItem("unitime_access", data.access);
          error.config._retry = true;
          error.config.headers.Authorization = `Bearer ${data.access}`;
          return api.request(error.config);
        } catch {
          localStorage.removeItem("unitime_access");
          localStorage.removeItem("unitime_refresh");
        }
      }
    }
    return Promise.reject(error);
  }
);

export type Paginated<T> = { count: number; next: string | null; previous: string | null; results: T[] };
