/**
 * Axios adapter that handles requests entirely in the browser, mimicking the
 * Django REST API surface used by this project. Activated when no
 * VITE_API_URL is configured (i.e. running in the Lovable preview).
 */
import type { AxiosAdapter, AxiosResponse, InternalAxiosRequestConfig } from "axios";
import { table, nextId, save, audit, enrich, resetDb, type Row } from "./db";
import { generateTimetable } from "./solver";

type TableName = Parameters<typeof table>[0];

// Map URL pluralized endpoints to internal table names
const RESOURCE_MAP: Record<string, TableName> = {
  faculties: "faculties",
  departments: "departments",
  programmes: "programmes",
  courses: "courses",
  semesters: "semesters",
  "academic-years": "academic_years",
  lecturers: "lecturers",
  rooms: "rooms",
  "student-groups": "student_groups",
  "time-slots": "time_slots",
  equipment: "equipment",
  notifications: "notifications",
};

function ok<T>(data: T, config: InternalAxiosRequestConfig, status = 200): AxiosResponse<T> {
  return {
    data, status, statusText: "OK", headers: {}, config,
    request: undefined,
  } as AxiosResponse<T>;
}

function err(status: number, body: any, config: InternalAxiosRequestConfig) {
  const e: any = new Error(typeof body === "string" ? body : JSON.stringify(body));
  e.response = { status, data: body, headers: {}, config, statusText: "ERR" };
  e.config = config; e.isAxiosError = true;
  throw e;
}

function paginate<T>(rows: T[]): { count: number; next: null; previous: null; results: T[] } {
  return { count: rows.length, next: null, previous: null, results: rows };
}

function matchesSearch(row: Row, term: string): boolean {
  if (!term) return true;
  const lc = term.toLowerCase();
  return Object.values(row).some((v) =>
    typeof v === "string" && v.toLowerCase().includes(lc) ||
    typeof v === "number" && String(v).includes(lc)
  );
}

function applyMutation(name: TableName, body: any, id?: number): Row {
  const t = table(name) as Row[];
  if (id != null) {
    const i = t.findIndex((r) => r.id === id);
    if (i < 0) throw { status: 404 };
    t[i] = { ...t[i], ...body, id: t[i].id };
    enrich(); save();
    audit("update", name, id, body);
    return t[i];
  }
  const created: Row = { ...body, id: nextId(name) };
  t.push(created);
  enrich(); save();
  audit("create", name, created.id, body);
  return created;
}

async function delay(ms = 80) { await new Promise((r) => setTimeout(r, ms)); }

export const mockAdapter: AxiosAdapter = async (config) => {
  await delay();
  const rawUrl = (config.url || "").replace(/^\/+|\/+$/g, "");
  // strip leading "api/" if any
  const url = rawUrl.replace(/^api\//, "");
  const method = (config.method || "get").toLowerCase();
  const body = (() => {
    try { return typeof config.data === "string" ? JSON.parse(config.data) : (config.data ?? {}); }
    catch { return {}; }
  })();
  const params = config.params ?? {};

  try {
    // ─────────────────────────── AUTH ───────────────────────────
    if (url === "auth/login" && method === "post") {
      const { username, password } = body;
      const u = table("users").find((x) => x.username === username);
      if (!u || u.password !== password) return err(401, { detail: "Invalid credentials" }, config);
      const access = `mock.${btoa(JSON.stringify({ sub: u.id, exp: Date.now() + 3600_000 }))}.sig`;
      const refresh = `mock-refresh-${u.id}`;
      const { password: _pw, ...safe } = u;
      return ok({ access, refresh, user: safe }, config);
    }
    if (url === "auth/refresh" && method === "post") {
      return ok({ access: `mock.${btoa(JSON.stringify({ exp: Date.now() + 3600_000 }))}.sig` }, config);
    }
    if (url === "auth/me" && method === "get") {
      const hdr = (config.headers?.Authorization || "") as string;
      const m = /mock\.([^.]+)\./.exec(hdr);
      if (!m) return err(401, { detail: "Unauthorized" }, config);
      try {
        const { sub } = JSON.parse(atob(m[1]));
        const u = table("users").find((x) => x.id === sub);
        if (!u) return err(401, { detail: "Unauthorized" }, config);
        const { password: _pw, ...safe } = u;
        return ok(safe, config);
      } catch { return err(401, { detail: "Unauthorized" }, config); }
    }
    if (url === "auth/logout") return ok({ detail: "logged out" }, config);

    // ───────────────── Generic resource CRUD ─────────────────
    for (const [seg, tname] of Object.entries(RESOURCE_MAP)) {
      if (url === seg && method === "get") {
        const all = (table(tname) as Row[]).slice();
        const filtered = all.filter((r) => matchesSearch(r, params.search ?? ""));
        return ok(paginate(filtered), config);
      }
      if (url === seg && method === "post") {
        const created = applyMutation(tname, body);
        return ok(created, config, 201);
      }
      const m = new RegExp(`^${seg}/(\\d+)$`).exec(url);
      if (m) {
        const id = Number(m[1]);
        const row = (table(tname) as Row[]).find((r) => r.id === id);
        if (method === "get") {
          if (!row) return err(404, { detail: "Not found" }, config);
          return ok(row, config);
        }
        if (method === "patch" || method === "put") {
          try { return ok(applyMutation(tname, body, id), config); }
          catch (e: any) { return err(404, { detail: "Not found" }, config); }
        }
        if (method === "delete") {
          const arr = table(tname) as Row[];
          const i = arr.findIndex((r) => r.id === id);
          if (i < 0) return err(404, { detail: "Not found" }, config);
          arr.splice(i, 1); enrich(); save();
          audit("delete", tname, id);
          return ok(null, config, 204);
        }
      }
      // notification mark-as-read shortcut
      const nMark = /^notifications\/(\d+)\/read$/.exec(url);
      if (nMark && method === "post") {
        const id = Number(nMark[1]);
        const n = table("notifications").find((x) => x.id === id);
        if (n) { n.read = true; save(); }
        return ok(n ?? null, config);
      }
    }

    // ───────────────── TIMETABLES ─────────────────
    if (url === "timetables" && method === "get") {
      const tts = table("timetables").slice().sort((a, b) => b.id - a.id);
      return ok(paginate(tts), config);
    }
    const ttDetail = /^timetables\/(\d+)$/.exec(url);
    if (ttDetail && method === "get") {
      const id = Number(ttDetail[1]);
      const t = table("timetables").find((x) => x.id === id);
      if (!t) return err(404, { detail: "Not found" }, config);
      const entries = table("timetable_entries").filter((e) => e.timetable === id);
      return ok({ ...t, entries }, config);
    }
    const ttDelete = /^timetables\/(\d+)$/.exec(url);
    if (ttDelete && method === "delete") {
      const id = Number(ttDelete[1]);
      const tts = table("timetables"); const i = tts.findIndex((x) => x.id === id);
      if (i < 0) return err(404, { detail: "Not found" }, config);
      tts.splice(i, 1);
      const entries = table("timetable_entries");
      for (let k = entries.length - 1; k >= 0; k--) if (entries[k].timetable === id) entries.splice(k, 1);
      save(); audit("delete", "timetables", id);
      return ok(null, config, 204);
    }
    // workflow actions
    const ttAction = /^timetables\/(\d+)\/(submit_for_approval|hod_approve|dean_approve|publish|reject)\/?$/.exec(url);
    if (ttAction && method === "post") {
      const id = Number(ttAction[1]); const action = ttAction[2];
      const t = table("timetables").find((x) => x.id === id);
      if (!t) return err(404, { detail: "Not found" }, config);
      const transitions: Record<string, string> = {
        submit_for_approval: "SUBMITTED",
        hod_approve: "HOD_APPROVED",
        dean_approve: "DEAN_APPROVED",
        publish: "PUBLISHED",
        reject: "DRAFT",
      };
      t.status = transitions[action];
      audit(action, "timetables", id);
      table("notifications").push({
        id: Date.now(), user: 1, title: `Timetable status: ${t.status}`,
        body: `"${t.name}" → ${t.status}`,
        level: action === "publish" ? "success" : "info",
        read: false, created_at: new Date().toISOString(),
      });
      save();
      return ok({ status: t.status }, config);
    }
    // manual entry move (drag-drop)
    const moveEntry = /^timetable-entries\/(\d+)\/move$/.exec(url);
    if (moveEntry && method === "post") {
      const id = Number(moveEntry[1]);
      const entries = table("timetable_entries");
      const e = entries.find((x) => x.id === id);
      if (!e) return err(404, { detail: "Not found" }, config);
      const { day, time_slot, room } = body;
      // basic clash check
      const clash = entries.find((x) => x.id !== id && x.timetable === e.timetable && x.day === day && x.time_slot === time_slot && (
        x.room === (room ?? e.room) ||
        x.lecturer === e.lecturer ||
        (x.student_groups ?? []).some((g: number) => (e.student_groups ?? []).includes(g))
      ));
      if (clash) return err(409, { detail: "Clash detected", clash_id: clash.id }, config);
      e.day = day; e.time_slot = time_slot;
      if (room) {
        e.room = room;
        const r = table("rooms").find((rr) => rr.id === room);
        e.room_code = r?.code ?? e.room_code;
      }
      audit("move", "timetable_entries", id, body);
      save();
      return ok(e, config);
    }

    // generation
    if ((url === "timetable/generate" || url === "timetables/generate") && method === "post") {
      const result = generateTimetable({
        semester_id: Number(body.semester_id),
        name: String(body.name ?? "Generated timetable"),
      });
      return ok(result, config);
    }

    // ───────────────── REPORTS ─────────────────
    if (url === "reports/dashboard" && method === "get") {
      enrich();
      const tts = table("timetables");
      return ok({
        faculties: table("faculties").length,
        departments: table("departments").length,
        programmes: table("programmes").length,
        courses: table("courses").length,
        lecturers: table("lecturers").length,
        rooms: table("rooms").length,
        student_groups: table("student_groups").length,
        timetables: tts.length,
        published_timetables: tts.filter((t) => t.status === "PUBLISHED").length,
      }, config);
    }
    if (url === "reports/workloads" && method === "get") {
      enrich();
      const allocs = table("course_allocations");
      const courses = table("courses");
      const out = table("lecturers").map((l) => {
        const hours = allocs
          .filter((a) => a.lecturer === l.id)
          .reduce((sum, a) => sum + (courses.find((c) => c.id === a.course)?.weekly_hours ?? 0), 0);
        const cap = Number(l.max_weekly_hours ?? 22);
        const util = Math.round((hours / cap) * 100);
        return { name: l.name, rank: l.rank, hours, max_hours: cap, utilization: util, overloaded: hours > cap };
      });
      return ok(out, config);
    }
    if (url === "reports/room-utilization" && method === "get") {
      const entries = table("timetable_entries");
      const slotCount = table("time_slots").filter((s) => !s.is_lunch).length;
      const dayCount = 6;
      const totalSlots = slotCount * dayCount;
      const out = table("rooms").map((r) => {
        const sessions = entries.filter((e) => e.room === r.id).length;
        const util = totalSlots > 0 ? Math.round((sessions / totalSlots) * 100) : 0;
        return { code: r.code, type: r.room_type, capacity: r.capacity, sessions, utilization: util };
      });
      return ok(out, config);
    }
    if (url === "reports/clashes" && method === "get") {
      const entries = table("timetable_entries");
      const room: any[] = []; const lec: any[] = []; const grp: any[] = [];
      const seen = new Map<string, any>();
      for (const e of entries) {
        const k = `${e.day}-${e.time_slot}`;
        const bucket = seen.get(k) ?? []; bucket.push(e); seen.set(k, bucket);
      }
      for (const bucket of seen.values()) {
        for (let i = 0; i < bucket.length; i++) for (let j = i + 1; j < bucket.length; j++) {
          const a = bucket[i], b = bucket[j];
          if (a.timetable !== b.timetable) continue;
          if (a.room === b.room) room.push({ a: a.id, b: b.id, room: a.room_code });
          if (a.lecturer === b.lecturer) lec.push({ a: a.id, b: b.id, lecturer: a.lecturer_name });
          const overlap = (a.student_groups ?? []).filter((g: number) => (b.student_groups ?? []).includes(g));
          if (overlap.length) grp.push({ a: a.id, b: b.id, groups: overlap });
        }
      }
      return ok({ room_clashes: room, lecturer_clashes: lec, group_clashes: grp }, config);
    }
    if (url === "reports/student-days" && method === "get") {
      const entries = table("timetable_entries");
      const out = table("student_groups").map((g) => {
        const days = new Set<number>();
        let sessions = 0;
        for (const e of entries) if ((e.student_groups ?? []).includes(g.id)) { days.add(e.day); sessions++; }
        return { name: g.name, day_count: days.size, sessions };
      });
      return ok(out, config);
    }
    if (url === "reports/audit" && method === "get") {
      return ok(paginate(table("audit_logs").slice().reverse().slice(0, 100)), config);
    }

    // ───────────────── ADMIN ─────────────────
    if (url === "admin/reset" && method === "post") {
      resetDb();
      return ok({ ok: true }, config);
    }

    return err(404, { detail: `Mock endpoint not implemented: ${method.toUpperCase()} /${url}` }, config);
  } catch (e: any) {
    if (e?.isAxiosError) throw e;
    return err(500, { detail: e?.message ?? "Mock error" }, config);
  }
};
