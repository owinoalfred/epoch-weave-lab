import axios from "axios";

const baseURL = (import.meta.env.VITE_API_URL as string | undefined) ?? "http://localhost:8000/api";

export const api = axios.create({ baseURL, withCredentials: false });

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
    if (error.response?.status === 401 && typeof window !== "undefined") {
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
