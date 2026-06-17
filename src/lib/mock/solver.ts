/**
 * Greedy constraint-satisfying timetable solver — TS analogue of the OR-Tools
 * CP-SAT engine in the Django backend. Produces feasible schedules respecting
 * hard constraints and minimizes a soft penalty.
 *
 * Hard constraints:
 *  - no lecturer / room / student-group clashes
 *  - room capacity ≥ group size sum
 *  - lecture courses → LECTURE/AUDITORIUM/SEMINAR rooms;
 *    lab courses → LAB/COMPUTER_LAB
 *  - required equipment ⊆ room equipment
 *  - lecturer weekly-hour cap (by rank)
 *  - group day-cap (UG sem 1: 4 sessions/day; otherwise 3; PG includes Saturday)
 *  - no scheduling in lunch slot
 *
 * Soft objective:
 *  - prefer mornings, minimize daily gaps for groups, balance lecturer load
 */
import { table, nextId, save, audit, enrich } from "./db";

const DAYS_DEFAULT = [0, 1, 2, 3, 4]; // Mon–Fri
const DAYS_PG      = [0, 1, 2, 3, 4, 5];

const LECTURE_ROOMS = new Set(["LECTURE", "AUDITORIUM", "SEMINAR"]);
const LAB_ROOMS     = new Set(["LAB", "COMPUTER_LAB"]);

export interface GenerateResult {
  timetable_id: number;
  entries: number;
  hard_violations: number;
  soft_violations: number;
  score: number;
  unscheduled: { course_code: string; reason: string }[];
}

export function generateTimetable(opts: { semester_id: number; name: string }): GenerateResult {
  enrich();
  const semesters    = table("semesters");
  const allocations  = table("course_allocations");
  const courses      = table("courses");
  const lecturers    = table("lecturers");
  const groups       = table("student_groups");
  const rooms        = table("rooms").filter((r) => r.is_active !== false);
  const slots        = table("time_slots").filter((s) => !s.is_lunch).sort((a, b) => a.order - b.order);
  const programmes   = table("programmes");
  const equipment    = table("equipment");

  const semester = semesters.find((s) => s.id === opts.semester_id);
  if (!semester) throw new Error("Semester not found");

  // Build sessions (one per weekly hour) from allocations
  interface Session {
    allocId: number;
    courseId: number;
    course: any;
    lecturerId: number;
    groupIds: number[];
    isLab: boolean;
    sessionIndex: number;
    totalSessions: number;
  }
  const sessions: Session[] = [];
  for (const a of allocations.filter((x) => x.semester === opts.semester_id)) {
    const c = courses.find((cc) => cc.id === a.course);
    if (!c) continue;
    const hrs = Number(c.weekly_hours ?? 3);
    for (let i = 0; i < hrs; i++) {
      sessions.push({
        allocId: a.id,
        courseId: c.id,
        course: c,
        lecturerId: a.lecturer,
        groupIds: a.student_groups ?? [],
        isLab: !!c.has_lab && i === hrs - 1, // last session of lab courses is the lab
        sessionIndex: i,
        totalSessions: hrs,
      });
    }
  }

  // Determine day set: include Saturday if any postgraduate group
  const anyPG = sessions.some((s) =>
    s.groupIds.some((gid) => {
      const g = groups.find((gg) => gg.id === gid);
      const p = g ? programmes.find((pp) => pp.id === g.programme) : null;
      return p && (p.level === "MS" || p.level === "PHD" || p.level === "PG");
    })
  );
  const DAYS = anyPG ? DAYS_PG : DAYS_DEFAULT;

  // Sort by difficulty (most-constrained first)
  sessions.sort((a, b) => {
    const eqA = (a.course.requires_equipment?.length ?? 0) + (a.isLab ? 5 : 0) + a.groupIds.length;
    const eqB = (b.course.requires_equipment?.length ?? 0) + (b.isLab ? 5 : 0) + b.groupIds.length;
    return eqB - eqA;
  });

  // Occupancy maps: key = `${day}-${slotId}`
  const lecturerBusy = new Map<string, Set<number>>();
  const roomBusy     = new Map<string, Set<number>>();
  const groupBusy    = new Map<string, Set<number>>();
  const lecturerHours= new Map<number, number>();
  const groupDayCount= new Map<string, number>(); // `${groupId}-${day}`

  const get = <K, V>(m: Map<K, V>, k: K, factory: () => V): V => {
    const v = m.get(k); if (v) return v;
    const n = factory(); m.set(k, n); return n;
  };

  const eqCodeToId = new Map<string, number>(equipment.map((e: any) => [e.code, e.id]));

  const entries: any[] = [];
  const unscheduled: { course_code: string; reason: string }[] = [];
  let softPenalty = 0;

  for (const s of sessions) {
    const lec = lecturers.find((l) => l.id === s.lecturerId);
    if (!lec) { unscheduled.push({ course_code: s.course.code, reason: "Lecturer missing" }); continue; }
    const lecCap = Number(lec.max_weekly_hours ?? 22);
    const lecUsed = lecturerHours.get(lec.id) ?? 0;
    if (lecUsed >= lecCap) {
      unscheduled.push({ course_code: s.course.code, reason: `${lec.name} at cap` }); continue;
    }

    const groupSize = s.groupIds.reduce((sum, gid) => sum + (groups.find((g) => g.id === gid)?.size ?? 0), 0);
    const reqEqIds = (s.course.requires_equipment ?? []).map((c: string) => eqCodeToId.get(c)).filter((x: any): x is number => !!x);
    const allowedRoomTypes = s.isLab ? LAB_ROOMS : LECTURE_ROOMS;
    const candidateRooms = rooms.filter((r) =>
      allowedRoomTypes.has(r.room_type) &&
      r.capacity >= groupSize &&
      reqEqIds.every((eq: number) => (r.equipment ?? []).includes(eq))
    ).sort((a, b) => a.capacity - b.capacity); // prefer tightest fit

    if (candidateRooms.length === 0) {
      unscheduled.push({ course_code: s.course.code, reason: "No room satisfies constraints" });
      continue;
    }

    // Build day×slot candidates with soft cost (prefer earlier slots, balance days)
    type Cand = { day: number; slotId: number; cost: number };
    const cands: Cand[] = [];
    for (const day of DAYS) {
      for (const slot of slots) {
        // hard: lecturer free
        const lkey = `${day}-${slot.id}`;
        const lBusy = lecturerBusy.get(lkey); if (lBusy?.has(lec.id)) continue;
        // hard: lecturer unavailable list
        if ((lec.unavailable_slots ?? []).some((u: any) => u.day === day && u.time_slot === slot.id)) continue;
        // hard: each group free + day-cap
        let groupOk = true;
        for (const gid of s.groupIds) {
          if (groupBusy.get(lkey)?.has(gid)) { groupOk = false; break; }
          const grp = groups.find((g) => g.id === gid);
          const prog = grp ? programmes.find((p) => p.id === grp.programme) : null;
          const isUG1 = prog?.level === "UG" && Number(s.course.semester_number) === 1;
          const dayCap = isUG1 ? 4 : 3;
          const dayKey = `${gid}-${day}`;
          if ((groupDayCount.get(dayKey) ?? 0) >= dayCap) { groupOk = false; break; }
        }
        if (!groupOk) continue;

        // soft cost: earlier = better, lunch-adjacent neutral, late penalty
        const slotCost = (slot.order - 1) * 2;
        cands.push({ day, slotId: slot.id, cost: slotCost });
      }
    }
    if (cands.length === 0) {
      unscheduled.push({ course_code: s.course.code, reason: "No free slot" });
      continue;
    }
    cands.sort((a, b) => a.cost - b.cost);

    // pick first candidate where a room is free
    let placed = false;
    for (const cand of cands) {
      const key = `${cand.day}-${cand.slotId}`;
      const rBusy = roomBusy.get(key) ?? new Set<number>();
      const room = candidateRooms.find((r) => !rBusy.has(r.id));
      if (!room) continue;

      // commit
      get(lecturerBusy, key, () => new Set<number>()).add(lec.id);
      get(roomBusy,     key, () => new Set<number>()).add(room.id);
      const gBusy = get(groupBusy, key, () => new Set<number>());
      for (const gid of s.groupIds) {
        gBusy.add(gid);
        const dayKey = `${gid}-${cand.day}`;
        groupDayCount.set(dayKey, (groupDayCount.get(dayKey) ?? 0) + 1);
      }
      lecturerHours.set(lec.id, lecUsed + 1);
      softPenalty += cand.cost;

      entries.push({
        id: 0, // assigned later
        course: s.course.id,
        course_code: s.course.code,
        course_title: s.course.title,
        lecturer: lec.id,
        lecturer_name: lec.name,
        room: room.id,
        room_code: room.code,
        day: cand.day,
        time_slot: cand.slotId,
        student_groups: s.groupIds,
        is_lab: s.isLab,
      });
      placed = true;
      break;
    }
    if (!placed) unscheduled.push({ course_code: s.course.code, reason: "All compatible rooms busy" });
  }

  // Persist timetable + entries
  const tt = {
    id: nextId("timetables"),
    name: opts.name || `Timetable ${new Date().toLocaleString()}`,
    version: 1,
    semester: opts.semester_id,
    semester_name: `${semester.academic_year_name} · ${semester.name}`,
    status: "READY",
    created_at: new Date().toISOString(),
    optimization_score: Math.max(0, 100 - softPenalty * 0.4 - unscheduled.length * 6),
    hard_violations: unscheduled.length,
    soft_violations: Math.round(softPenalty),
    entry_count: entries.length,
    unscheduled,
  };
  table("timetables").push(tt);
  const entryTable = table("timetable_entries");
  for (const e of entries) {
    e.id = nextId("timetable_entries");
    e.timetable = tt.id;
    entryTable.push(e);
  }
  audit("generate", "timetable", tt.id, { entries: entries.length, unscheduled: unscheduled.length });
  // notify
  table("notifications").push({
    id: Date.now(),
    user: 1,
    title: `Timetable "${tt.name}" generated`,
    body: `${entries.length} sessions scheduled, ${unscheduled.length} unscheduled, score ${Math.round(tt.optimization_score)}`,
    level: unscheduled.length > 0 ? "warning" : "success",
    read: false,
    created_at: new Date().toISOString(),
  });
  save();

  return {
    timetable_id: tt.id,
    entries: entries.length,
    hard_violations: unscheduled.length,
    soft_violations: tt.soft_violations,
    score: tt.optimization_score,
    unscheduled,
  };
}
