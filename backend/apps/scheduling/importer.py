import logging
import re
from typing import Dict, List, Tuple, Any
import pandas as pd
from django.db import transaction
from django.utils import timezone

from apps.academics.models import Programme, StudentGroup, Course, Term
from apps.staff.models import Lecturer
from apps.facilities.models import Room
from apps.scheduling.models import TimeSlot, DayOfWeek

logger = logging.getLogger(__name__)

# ─── NORMALIZATION MAPS ─────────────────────────────────────────────────────
DAY_MAP = {
    "MON": DayOfWeek.MONDAY, "MONDAY": DayOfWeek.MONDAY,
    "TUE": DayOfWeek.TUESDAY, "TUESDAY": DayOfWeek.TUESDAY,
    "WED": DayOfWeek.WEDNESDAY, "WEDNESDAY": DayOfWeek.WEDNESDAY,
    "THU": DayOfWeek.THURSDAY, "THUR": DayOfWeek.THURSDAY, "THURSDAY": DayOfWeek.THURSDAY,
    "FRI": DayOfWeek.FRIDAY, "FRIDAY": DayOfWeek.FRIDAY,
    "SAT": DayOfWeek.SATURDAY, "SATURDAY": DayOfWeek.SATURDAY,
}

# Added "11:00AM - 12:00PM" based on the BSCAF BIB1104 data in your Excel
TIME_SLOT_MAP = {
    "9:00AM - 10:55AM": 1, "09:00AM - 10:55AM": 1, "9:00AM-10:55AM": 1, "9:00-10:55": 1,
    "11:05AM - 1:00PM": 2, "11:05AM-1:00PM": 2, "11:05-1:00": 2, "11:00AM - 12:55PM": 2,
    "11:00AM - 12:00PM": 2, # Minor formatting variation found in BSCAF data
    "2:00PM - 3:55PM": 3, "2:00PM-3:55PM": 3, "2:00-3:55": 3,
    "4:05PM - 6:00PM": 4, "4:05-6:00": 4, "4:05PM-6:00PM": 4,
    "5:45PM - 8:00PM": 5,  # Evening slot
}

# Updated aliases to handle the exact trailing spaces found in your "Load" sheet
FACULTY_ALIASES = {
    "Dennis Gabawaya": ["DENNIS GABAWAYA", "DENNIS GABEWAYA", "Denis Gebawaya", "Denis Gebewaya", "Dennis Gebewaya"],
    "Faisal Mutunzi": ["FAISAL MUTUNZI", "FAISAL MUTUNZ"],
    "Giulio Molfese": ["GIULIO MOLFESE", "GULIO MOLFESE", "MOLFESE GIULIO", "Gulio Molfese"],
    "Collin Atwiine": ["COLLIN ATWIINE", "COLLIN"],
    "Umesh Kumar": ["UMESH KUMAR", "KUMAR UMESH"],
    "Sajjad Surve": ["SAJJAD SURVE", "SAJJAD", "SURVE SAJJAD"],
    "John Ochen": ["JOHN OCHEN", "JOHN OCHEN "],
    "Martin Mugenyi": ["MARTIN MUGENYI", "MARTIN MUGENYI "],
    "Nyaurah Emmanuel": ["NYAURAH EMMANUEL", "NYAURAH EMMANUEL "],
    "S Amrutha": ["S AMRUTHA", "S AMRUTHA "],
    "Nsuguba Tom": ["NSUBUGA TOM", "NSUBUGA TOM "],
    "P Ilavarasan": ["P ILAVARASAN", "P ILAVARASAN "],
    "Ronald Ssemanda": ["RONALD SSEMANDA", "RONALD SSEMANDA  "], # Handles the double space in your Excel
}

def normalize_day(raw: str) -> int | None:
    if not raw: return None
    return DAY_MAP.get(str(raw).strip().upper())

def normalize_time(raw: str) -> int | None:
    if not raw: return None
    cleaned = str(raw).strip().upper()
    return TIME_SLOT_MAP.get(cleaned)

def normalize_faculty(raw: str) -> str:
    if not raw or str(raw).strip().upper() in ["X", "TBA", "-", "N/A", ""]:
        return "UNKNOWN"
    
    # Clean the string: strip ALL spaces, uppercase for matching
    cleaned = str(raw).strip()
    upper_cleaned = cleaned.upper()
    
    # Check against aliases
    for canonical, aliases in FACULTY_ALIASES.items():
        if upper_cleaned == canonical.upper() or upper_cleaned in [a.upper().strip() for a in aliases]:
            return canonical # Return the nicely formatted canonical name
            
    # If not found, return the cleaned string (Title Cased)
    return cleaned.title()

def normalize_room(raw: str) -> str:
    if not raw: return "UNASSIGNED"
    return str(raw).strip().upper()

# ─── CLASH DETECTOR ─────────────────────────────────────────────────────────
def detect_clashes(rows: List[Dict[str, Any]]) -> Dict[str, List[Dict]]:
    clashes = {"room": [], "lecturer": [], "student_group": []}
    seen_rooms: Dict[Tuple[int, int, int], List[int]] = {}
    seen_lecturers: Dict[Tuple[int, int, int], List[int]] = {}
    seen_groups: Dict[Tuple[int, int, int], List[int]] = {}

    for idx, row in enumerate(rows):
        room_key = (row.get("room_db_id"), row["day"], row["slot_id"])
        lec_key = (row.get("lecturer_db_id"), row["day"], row["slot_id"])
        grp_key = (row["group_db_id"], row["day"], row["slot_id"])

        if room_key[0] and room_key in seen_rooms:
            clashes["room"].append({"row": idx + 2, "room": row["room_code"], "day": row["day_name"], "slot": row["time_raw"], "conflicts_with": seen_rooms[room_key]})
        seen_rooms[room_key] = seen_rooms.get(room_key, []) + [idx + 2]

        if lec_key[0] and lec_key in seen_lecturers:
            clashes["lecturer"].append({"row": idx + 2, "lecturer": row["faculty"], "day": row["day_name"], "slot": row["time_raw"], "conflicts_with": seen_lecturers[lec_key]})
        seen_lecturers[lec_key] = seen_lecturers.get(lec_key, []) + [idx + 2]

        if grp_key[0] and grp_key in seen_groups:
            clashes["student_group"].append({"row": idx + 2, "group": row["batch_code"], "day": row["day_name"], "slot": row["time_raw"], "conflicts_with": seen_groups[grp_key]})
        seen_groups[grp_key] = seen_groups.get(grp_key, []) + [idx + 2]

    return clashes

# ─── MAIN IMPORTER ──────────────────────────────────────────────────────────
def parse_draft_timetable(file_path: str) -> Dict[str, Any]:
    logger.info(f"Parsing draft timetable: {file_path}")
    
    try:
        df = pd.read_excel(file_path, sheet_name="Time Table", engine="openpyxl")
    except Exception as e:
        return {"error": f"Failed to read Excel: {str(e)}"}

    df.columns = [str(c).strip() for c in df.columns]
    required_cols = ["BATCHCODE", "WDAY", "Time", "UNITCODE", "UNITNAME", "Faculty", "ROOMCODE"]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        return {"error": f"Missing required columns: {missing}"}

    df = df.dropna(subset=["BATCHCODE", "WDAY", "Time"])
    cleaned_rows = []
    warnings = []

    for idx, row in df.iterrows():
        excel_row_num = idx + 2
        try:
            day = normalize_day(row["WDAY"])
            slot_id = normalize_time(row["Time"])
            if day is None or slot_id is None:
                warnings.append({"row": excel_row_num, "type": "INVALID_DAY_OR_TIME", "msg": f"Day: {row['WDAY']}, Time: {row['Time']}"})
                continue

            faculty = normalize_faculty(row.get("Faculty", ""))
            room_code = normalize_room(row.get("ROOMCODE", ""))
            batch_code = str(row["BATCHCODE"]).strip()
            unit_code = str(row["UNITCODE"]).strip()

            group = StudentGroup.objects.filter(code=batch_code).first()
            lecturer = Lecturer.objects.filter(name__iexact=faculty).first() if faculty != "UNKNOWN" else None
            room = Room.objects.filter(code__iexact=room_code).first() if room_code != "UNASSIGNED" else None

            # Safer Head Count parsing to prevent crashes on text/empty cells
            head_count = 0
            try:
                raw_hc = row.get("Head Count")
                if pd.notna(raw_hc):
                    head_count = int(float(raw_hc))
            except (ValueError, TypeError):
                warnings.append({"row": excel_row_num, "type": "INVALID_HEAD_COUNT", "msg": f"Invalid Head Count: {raw_hc}"})

            cleaned_rows.append({
                "excel_row": excel_row_num,
                "batch_code": batch_code,
                "unit_code": unit_code,
                "unit_name": row.get("UNITNAME", ""),
                "day": day,
                "day_name": row["WDAY"],
                "slot_id": slot_id,
                "time_raw": row["Time"],
                "faculty": faculty,
                "room_code": room_code,
                "group_db_id": group.id if group else None,
                "lecturer_db_id": lecturer.id if lecturer else None,
                "room_db_id": room.id if room else None,
                "head_count": head_count,
            })

            if not group:
                warnings.append({"row": excel_row_num, "type": "MISSING_GROUP", "msg": f"Batch {batch_code} not in DB"})
            if not lecturer and faculty != "UNKNOWN":
                warnings.append({"row": excel_row_num, "type": "MISSING_LECTURER", "msg": f"Lecturer {faculty} not in DB"})
            if not room and room_code != "UNASSIGNED" and "ONLINE" not in room_code:
                warnings.append({"row": excel_row_num, "type": "MISSING_ROOM", "msg": f"Room {room_code} not in DB"})

        except Exception as e:
            warnings.append({"row": excel_row_num, "type": "PARSE_ERROR", "msg": str(e)})

    clashes = detect_clashes(cleaned_rows)
    
    return {
        "success": True,
        "total_rows": len(df),
        "cleaned_rows": len(cleaned_rows),
        "warnings": warnings,
        "clashes": clashes,
        "data": cleaned_rows[:50]
    }

# ─── ROOM CAPACITY IMPORTER (NEW) ───────────────────────────────────────────
def parse_room_capacity(file_path: str) -> Dict[str, Any]:
    """
    Parses the 'Room Capacity' sheet, ignoring floor headers (merged cells),
    and extracts room codes and their capacities.
    """
    logger.info(f"Parsing room capacities: {file_path}")
    try:
        # Read without headers to easily navigate the merged cells
        df = pd.read_excel(file_path, sheet_name="Room Capacity", header=None, engine="openpyxl")
    except Exception as e:
        return {"error": f"Failed to read Room Capacity sheet: {str(e)}"}

    rooms = []
    for idx, row in df.iterrows():
        col0 = str(row.iloc[0]).strip() if pd.notna(row.iloc[0]) else ""
        col1 = str(row.iloc[1]).strip() if pd.notna(row.iloc[1]) else ""
        
        # Match standard room codes (e.g., "104", "203", "B101")
        # We use a regex that captures the first valid room code format
        match = re.match(r'^(\d{3}|B\d{3})', col0)
        if match:
            room_code = match.group(1)
            try:
                capacity = int(float(col1))
                rooms.append({"code": room_code, "capacity": capacity})
            except ValueError:
                pass # Ignore rows where capacity is not a number
                
    return {"success": True, "total_rooms": len(rooms), "rooms": rooms}