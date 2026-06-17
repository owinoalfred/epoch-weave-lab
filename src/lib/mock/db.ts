/**
 * In-browser mock database for UniTime — mirrors the Django REST surface.
 * Persisted to localStorage so refreshes keep state.
 */

const KEY = "unitime_mockdb_v2";

export type Row = Record<string, any> & { id: number };

interface Tables {
  users: Row[];
  academic_years: Row[];
  semesters: Row[];
  faculties: Row[];
  departments: Row[];
  programmes: Row[];
  courses: Row[];
  student_groups: Row[];
  lecturers: Row[];
  course_allocations: Row[];
  rooms: Row[];
  equipment: Row[];
  time_slots: Row[];
  timetables: Row[];
  timetable_entries: Row[];
  notifications: Row[];
  audit_logs: Row[];
}

const empty: Tables = {
  users: [], academic_years: [], semesters: [], faculties: [], departments: [],
  programmes: [], courses: [], student_groups: [], lecturers: [], course_allocations: [],
  rooms: [], equipment: [], time_slots: [], timetables: [], timetable_entries: [],
  notifications: [], audit_logs: [],
};

let db: Tables = loadOrSeed();

function loadOrSeed(): Tables {
  if (typeof window === "undefined") return seed();
  try {
    const raw = localStorage.getItem(KEY);
    if (raw) return JSON.parse(raw) as Tables;
  } catch {}
  const fresh = seed();
  try { localStorage.setItem(KEY, JSON.stringify(fresh)); } catch {}
  return fresh;
}

export function save() {
  if (typeof window === "undefined") return;
  try { localStorage.setItem(KEY, JSON.stringify(db)); } catch {}
}

export function resetDb() {
  db = seed();
  save();
}

export function table<K extends keyof Tables>(name: K): Tables[K] {
  return db[name];
}

let _seq = 100000;
export function nextId(name: keyof Tables): number {
  const t = db[name];
  const maxIn = t.reduce((m, r) => Math.max(m, r.id ?? 0), 0);
  _seq = Math.max(_seq + 1, maxIn + 1);
  return _seq;
}

// ───────────────────────────── seed ─────────────────────────────
function seed(): Tables {
  const d: Tables = JSON.parse(JSON.stringify(empty));

  // Users
  d.users.push(
    { id: 1, username: "admin", email: "admin@uni.edu", first_name: "System", last_name: "Admin", roles: ["SUPER_ADMIN"], password: "admin12345" },
    { id: 2, username: "dean",  email: "dean@uni.edu",  first_name: "Alice",  last_name: "Mwesigwa", roles: ["DEAN"], password: "password123" },
    { id: 3, username: "hod",   email: "hod@uni.edu",   first_name: "Brian",  last_name: "Okello",   roles: ["HOD"], password: "password123" },
    { id: 4, username: "officer", email: "officer@uni.edu", first_name: "Carol", last_name: "Nansubuga", roles: ["TIMETABLE_OFFICER"], password: "password123" },
    { id: 5, username: "jdoe",  email: "jdoe@uni.edu",  first_name: "Jane",   last_name: "Doe",      roles: ["LECTURER"], password: "password123" },
  );

  // Academic year & semester
  d.academic_years.push({ id: 1, name: "2025/2026", start_date: "2025-08-01", end_date: "2026-07-31", is_active: true });
  d.semesters.push(
    { id: 1, academic_year: 1, academic_year_name: "2025/2026", name: "Semester 1", number: 1, start_date: "2025-08-15", end_date: "2025-12-15", is_active: true },
    { id: 2, academic_year: 1, academic_year_name: "2025/2026", name: "Semester 2", number: 2, start_date: "2026-01-15", end_date: "2026-05-30", is_active: false },
  );

  // Time slots (Mon–Sat × 5 daily blocks)
  d.time_slots.push(
    { id: 1, name: "Slot 1", start_time: "09:00", end_time: "10:55", order: 1, is_lunch: false },
    { id: 2, name: "Slot 2", start_time: "11:00", end_time: "13:00", order: 2, is_lunch: false },
    { id: 3, name: "Lunch",  start_time: "13:00", end_time: "14:00", order: 3, is_lunch: true  },
    { id: 4, name: "Slot 3", start_time: "14:00", end_time: "15:55", order: 4, is_lunch: false },
    { id: 5, name: "Slot 4", start_time: "16:00", end_time: "18:00", order: 5, is_lunch: false },
  );

  // Equipment
  d.equipment.push(
    { id: 1, code: "computers", name: "Computers" },
    { id: 2, code: "projector", name: "Projector" },
    { id: 3, code: "internet",  name: "Internet" },
    { id: 4, code: "whiteboard", name: "Whiteboard" },
  );

  // Faculties + departments + programmes
  d.faculties.push(
    { id: 1, code: "FOC", name: "Faculty of Computing", departments_count: 2 },
    { id: 2, code: "FOE", name: "Faculty of Engineering", departments_count: 1 },
    { id: 3, code: "FBM", name: "Faculty of Business & Management", departments_count: 1 },
  );
  d.departments.push(
    { id: 1, faculty: 1, faculty_name: "Faculty of Computing", code: "CS",  name: "Computer Science",      programmes_count: 2 },
    { id: 2, faculty: 1, faculty_name: "Faculty of Computing", code: "IS",  name: "Information Systems",   programmes_count: 1 },
    { id: 3, faculty: 2, faculty_name: "Faculty of Engineering", code: "EE", name: "Electrical Engineering", programmes_count: 1 },
    { id: 4, faculty: 3, faculty_name: "Faculty of Business & Management", code: "MGT", name: "Management", programmes_count: 1 },
  );
  d.programmes.push(
    { id: 1, department: 1, department_name: "Computer Science",      code: "BSCCS", name: "BSc Computer Science",       level: "UG", duration_years: 3 },
    { id: 2, department: 1, department_name: "Computer Science",      code: "MSCCS", name: "MSc Computer Science",       level: "MS", duration_years: 2 },
    { id: 3, department: 2, department_name: "Information Systems",   code: "BSCIS", name: "BSc Information Systems",    level: "UG", duration_years: 3 },
    { id: 4, department: 3, department_name: "Electrical Engineering",code: "BENGEE", name: "BEng Electrical Engineering",level: "UG", duration_years: 4 },
    { id: 5, department: 4, department_name: "Management",            code: "BBA",   name: "Bachelor of Business Admin", level: "UG", duration_years: 3 },
  );

  // Courses (programme-scoped)
  const courses: Array<[string, string, number, number, boolean, string[], number, number, number]> = [
    // code, title, cu, weekly_hours, has_lab, equipment, year, sem, programme
    ["CS101", "Introduction to Programming", 4, 4, true,  ["computers"], 1, 1, 1],
    ["CS102", "Discrete Mathematics",        3, 3, false, [],            1, 1, 1],
    ["CS103", "Computer Organisation",       3, 3, false, ["projector"], 1, 1, 1],
    ["CS201", "Data Structures",             4, 4, true,  ["computers"], 2, 1, 1],
    ["CS202", "Operating Systems",           3, 3, false, ["projector"], 2, 1, 1],
    ["CS301", "Software Engineering",        3, 3, false, ["projector"], 3, 1, 1],
    ["IS101", "Database Foundations",        3, 3, true,  ["computers"], 1, 1, 3],
    ["IS201", "Systems Analysis",            3, 3, false, [],            2, 1, 3],
    ["EE101", "Circuits I",                  4, 4, true,  [],            1, 1, 4],
    ["BBA101","Principles of Management",    3, 3, false, ["projector"], 1, 1, 5],
    ["MSCS501","Advanced Algorithms",        3, 3, false, ["projector"], 1, 1, 2],
  ];
  courses.forEach(([code, title, cu, hrs, lab, eq, year, sem, prog], i) => {
    const programme = d.programmes.find((p) => p.id === prog)!;
    d.courses.push({
      id: i + 1, programme: prog, programme_code: programme.code,
      code, title, credit_units: cu, weekly_hours: hrs,
      has_lab: lab, requires_equipment: eq,
      year_of_study: year, semester_number: sem,
    });
  });

  // Rooms
  d.rooms.push(
    { id: 1, code: "LR-101", name: "Lecture Room 101", building: "Block A", floor: "1", capacity: 120, room_type: "LECTURE",      equipment: [2,4], is_active: true },
    { id: 2, code: "LR-102", name: "Lecture Room 102", building: "Block A", floor: "1", capacity: 80,  room_type: "LECTURE",      equipment: [2,4], is_active: true },
    { id: 3, code: "LR-201", name: "Lecture Room 201", building: "Block A", floor: "2", capacity: 60,  room_type: "LECTURE",      equipment: [4],   is_active: true },
    { id: 4, code: "AUD-1",  name: "Main Auditorium",  building: "Block C", floor: "G", capacity: 300, room_type: "AUDITORIUM",   equipment: [2,3,4], is_active: true },
    { id: 5, code: "CLAB-01",name: "Computer Lab 1",   building: "Block B", floor: "G", capacity: 40,  room_type: "COMPUTER_LAB", equipment: [1,2,3], is_active: true },
    { id: 6, code: "CLAB-02",name: "Computer Lab 2",   building: "Block B", floor: "1", capacity: 40,  room_type: "COMPUTER_LAB", equipment: [1,2,3], is_active: true },
    { id: 7, code: "LAB-EE1",name: "EE Lab 1",         building: "Block D", floor: "G", capacity: 30,  room_type: "LAB",          equipment: [4],   is_active: true },
    { id: 8, code: "SEM-1",  name: "Seminar Room 1",   building: "Block A", floor: "2", capacity: 25,  room_type: "SEMINAR",      equipment: [4],   is_active: true },
  );

  // Student groups
  d.student_groups.push(
    { id: 1, programme: 1, programme_code: "BSCCS",  name: "BSCCS Y1 Group A", year_of_study: 1, size: 60 },
    { id: 2, programme: 1, programme_code: "BSCCS",  name: "BSCCS Y1 Group B", year_of_study: 1, size: 55 },
    { id: 3, programme: 1, programme_code: "BSCCS",  name: "BSCCS Y2",         year_of_study: 2, size: 50 },
    { id: 4, programme: 1, programme_code: "BSCCS",  name: "BSCCS Y3",         year_of_study: 3, size: 45 },
    { id: 5, programme: 3, programme_code: "BSCIS",  name: "BSCIS Y1",         year_of_study: 1, size: 40 },
    { id: 6, programme: 3, programme_code: "BSCIS",  name: "BSCIS Y2",         year_of_study: 2, size: 38 },
    { id: 7, programme: 4, programme_code: "BENGEE", name: "BENGEE Y1",        year_of_study: 1, size: 35 },
    { id: 8, programme: 5, programme_code: "BBA",    name: "BBA Y1",           year_of_study: 1, size: 80 },
    { id: 9, programme: 2, programme_code: "MSCCS",  name: "MSCCS Y1",         year_of_study: 1, size: 18 },
  );

  // Lecturers
  const rankCap: Record<string, number> = { LECTURER: 22, HOD: 16, DEAN: 12, LAB_ASSISTANT: 12 };
  const lecturerSeed = [
    ["STF001", "Dr.",  "Jane",    "Doe",        1, "LECTURER", 5],
    ["STF002", "Prof.","Brian",   "Okello",     1, "HOD",      3],
    ["STF003", "Dr.",  "Alice",   "Mwesigwa",   2, "DEAN",     2],
    ["STF004", "Mr.",  "Daniel",  "Kato",       1, "LECTURER", null],
    ["STF005", "Ms.",  "Esther",  "Namaganda",  1, "LECTURER", null],
    ["STF006", "Dr.",  "Frank",   "Ssemakula",  2, "LECTURER", null],
    ["STF007", "Mr.",  "George",  "Tumusiime",  3, "LECTURER", null],
    ["STF008", "Dr.",  "Helen",   "Akello",     4, "LECTURER", null],
    ["STF009", "Mr.",  "Isaac",   "Wamala",     1, "LAB_ASSISTANT", null],
  ];
  lecturerSeed.forEach(([staff_no, title, first, last, dept, rank, userId]: any, i) => {
    const deptRow = d.departments.find((dp) => dp.id === dept)!;
    d.lecturers.push({
      id: i + 1, staff_no, title, first_name: first, last_name: last,
      name: `${title} ${first} ${last}`,
      department: dept, department_name: deptRow.name,
      rank, max_weekly_hours: rankCap[rank], user: userId,
      unavailable_slots: [], // [{ day, time_slot }]
    });
  });

  // Course allocations (lecturer ↔ course ↔ groups for semester 1)
  const alloc = (lec: number, course: number, groups: number[]) => {
    d.course_allocations.push({
      id: d.course_allocations.length + 1,
      lecturer: lec, course, semester: 1, student_groups: groups,
    });
  };
  alloc(1, 1, [1, 2]);  // Jane Doe → CS101 → Y1 A&B
  alloc(1, 2, [1, 2]);  // Jane Doe → CS102 → Y1 A&B
  alloc(4, 3, [1, 2]);  // Daniel → CS103
  alloc(2, 4, [3]);     // Brian → CS201
  alloc(5, 5, [3]);     // Esther → CS202
  alloc(2, 6, [4]);     // Brian → CS301
  alloc(6, 7, [5]);     // Frank → IS101
  alloc(6, 8, [6]);     // Frank → IS201
  alloc(7, 9, [7]);     // George → EE101
  alloc(8, 10, [8]);    // Helen → BBA101
  alloc(3, 11, [9]);    // Alice (Dean) → MSCS501

  // Notifications
  d.notifications.push(
    { id: 1, user: 1, title: "Welcome to UniTime",
      body: "Demo mode active. All changes persist to localStorage. Reset from Settings.",
      level: "info", read: false, created_at: new Date().toISOString() },
    { id: 2, user: 1, title: "Sample data seeded",
      body: "3 faculties, 11 courses, 9 lecturers, 8 rooms, 9 student groups ready to schedule.",
      level: "success", read: false, created_at: new Date().toISOString() },
  );

  return d;
}

// ───────────────────────── audit helper ─────────────────────────
export function audit(action: string, entity: string, entity_id?: number, meta?: any) {
  db.audit_logs.push({
    id: db.audit_logs.length + 1,
    action, entity, entity_id, meta,
    actor: "demo",
    at: new Date().toISOString(),
  });
  if (db.audit_logs.length > 500) db.audit_logs.shift();
  save();
}

// ───────────────────────── enrichment ──────────────────────────
/** Recompute denormalized counts and joined display fields. */
export function enrich() {
  db.faculties.forEach((f) => { f.departments_count = db.departments.filter((d) => d.faculty === f.id).length; });
  db.departments.forEach((d) => {
    const f = db.faculties.find((x) => x.id === d.faculty);
    d.faculty_name = f?.name ?? "—";
    d.programmes_count = db.programmes.filter((p) => p.department === d.id).length;
  });
  db.programmes.forEach((p) => {
    const d = db.departments.find((x) => x.id === p.department);
    p.department_name = d?.name ?? "—";
  });
  db.courses.forEach((c) => {
    const p = db.programmes.find((x) => x.id === c.programme);
    c.programme_code = p?.code ?? "—";
  });
  db.student_groups.forEach((g) => {
    const p = db.programmes.find((x) => x.id === g.programme);
    g.programme_code = p?.code ?? "—";
  });
  db.lecturers.forEach((l) => {
    const d = db.departments.find((x) => x.id === l.department);
    l.department_name = d?.name ?? "—";
    l.name = `${l.title ?? ""} ${l.first_name ?? ""} ${l.last_name ?? ""}`.trim();
    const caps: Record<string, number> = { LECTURER: 22, HOD: 16, DEAN: 12, LAB_ASSISTANT: 12 };
    l.max_weekly_hours = caps[l.rank] ?? 22;
  });
  db.semesters.forEach((s) => {
    const y = db.academic_years.find((x) => x.id === s.academic_year);
    s.academic_year_name = y?.name ?? "—";
  });
}
enrich();
