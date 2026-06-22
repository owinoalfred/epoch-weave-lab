import logging
import re
from typing import Dict, List, Any
import pandas as pd
from django.db import transaction

logger = logging.getLogger(__name__)

# ─── NORMALIZATION MAPS ─────────────────────────────────────────────────────
DAY_MAP = {
    "MON": 0, "MONDAY": 0,
    "TUE": 1, "TUESDAY": 1,
    "WED": 2, "WEDNESDAY": 2,
    "THU": 3, "THUR": 3, "THURSDAY": 3,
    "FRI": 4, "FRIDAY": 4,
    "SAT": 5, "SATURDAY": 5,
}

TIME_SLOT_MAP = {
    "9:00AM - 10:55AM": 1, "09:00AM - 10:55AM": 1, "9:00AM-10:55AM": 1, "9:00-10:55": 1,
    "11:05AM - 1:00PM": 2, "11:05AM-1:00PM": 2, "11:05-1:00": 2, "11:00AM - 12:55PM": 2,
    "2:00PM - 3:55PM": 3, "2:00PM-3:55PM": 3, "2:00-3:55": 3,
    "4:05PM - 6:00PM": 4, "4:05-6:00": 4, "4:05PM-6:00PM": 4,
    "5:45PM - 8:00PM": 5, 
}

def normalize_day(raw: str) -> int | None:
    if not raw or str(raw).strip().upper() not in DAY_MAP: return None
    return DAY_MAP[str(raw).strip().upper()]

def normalize_time(raw: str) -> int | None:
    if not raw: return None
    cleaned = str(raw).strip().upper()
    return TIME_SLOT_MAP.get(cleaned)

def normalize_faculty(raw: str) -> str:
    if not raw or str(raw).strip().upper() in ["X", "TBA", "-", "N/A", "NONE", ""]:
        return "UNKNOWN"
    return str(raw).strip().title()

def normalize_room(raw: str) -> str:
    if not raw or str(raw).strip().upper() in ["NAN", "NONE", ""]:
        return "UNASSIGNED"
    return str(raw).strip().upper()

# ─── STRING-BASED CLASH DETECTOR ────────────────────────────────────────────
def detect_clashes(rows: List[Dict[str, Any]]) -> Dict[str, List[Dict]]:
    """
    Detects clashes using raw string codes instead of DB IDs.
    This allows us to see clashes immediately upon import, even if the DB is empty.
    """
    clashes = {"room": [], "lecturer": [], "student_group": []}
    
    seen_rooms = {}     # key: (room_code, day, slot_id) -> excel_row
    seen_lecturers = {} # key: (faculty_name, day, slot_id) -> excel_row
    seen_groups = {}    # key: (batch_code, day, slot_id) -> excel_row

    for row in rows:
        day = row["day"]
        slot_id = row["slot_id"]
        excel_row = row["excel_row"]
        
        # 1. Room Clashes (ignore unassigned rooms)
        room_code = row.get("room_code")
        if room_code and room_code not in ["UNASSIGNED", "NAN", "NONE"]:
            room_key = (room_code, day, slot_id)
            if room_key in seen_rooms:
                clashes["room"].append({
                    "row": excel_row, 
                    "room": room_code, 
                    "day": row["day_name"], 
                    "slot": row["time_raw"], 
                    "conflicts_with_row": seen_rooms[room_key]
                })
            else:
                seen_rooms[room_key] = excel_row

        # 2. Lecturer Clashes (ignore unknown/TBA)
        faculty = row.get("faculty")
        if faculty and faculty not in ["UNKNOWN", "TBA", "X"]:
            lec_key = (faculty.upper(), day, slot_id)
            if lec_key in seen_lecturers:
                clashes["lecturer"].append({
                    "row": excel_row, 
                    "lecturer": faculty, 
                    "day": row["day_name"], 
                    "slot": row["time_raw"], 
                    "conflicts_with_row": seen_lecturers[lec_key]
                })
            else:
                seen_lecturers[lec_key] = excel_row

        # 3. Student Group Clashes
        batch_code = row.get("batch_code")
        if batch_code and batch_code not in ["UNASSIGNED", "NAN", "NONE"]:
            grp_key = (batch_code.upper(), day, slot_id)
            if grp_key in seen_groups:
                clashes["student_group"].append({
                    "row": excel_row, 
                    "group": batch_code, 
                    "day": row["day_name"], 
                    "slot": row["time_raw"], 
                    "conflicts_with_row": seen_groups[grp_key]
                })
            else:
                seen_groups[grp_key] = excel_row

    return clashes

# ─── MAIN IMPORTER ──────────────────────────────────────────────────────────
def parse_draft_timetable(file_path: str) -> Dict[str, Any]:
    logger.info(f"Parsing draft timetable: {file_path}")
    
    try:
        # Skip the first row if it's just a title like "CLASSROOM SEATING CAPACITIES"
        df = pd.read_excel(file_path, sheet_name=0, engine="openpyxl")
    except Exception as e:
        return {"error": f"Failed to read Excel: {str(e)}"}

    # Clean columns
    df.columns = [str(c).strip() for c in df.columns]
    
    # Drop rows where essential scheduling info is missing
    df = df.dropna(subset=["BATCHCODE", "WDAY", "Time"])
    
    cleaned_rows = []
    warnings = []

    for idx, row in df.iterrows():
        excel_row_num = idx + 2
        try:
            day = normalize_day(row["WDAY"])
            slot_id = normalize_time(row["Time"])
            
            if day is None or slot_id is None:
                warnings.append({
                    "row": excel_row_num, 
                    "type": "INVALID_DAY_OR_TIME", 
                    "msg": f"Day: {row['WDAY']}, Time: {row['Time']}"
                })
                continue

            faculty = normalize_faculty(row.get("Faculty", ""))
            room_code = normalize_room(row.get("ROOMCODE", ""))
            batch_code = str(row["BATCHCODE"]).strip()
            unit_code = str(row["UNITCODE"]).strip()

            cleaned_rows.append({
                "excel_row": excel_row_num,
                "batch_code": batch_code,
                "unit_code": unit_code,
                "unit_name": str(row.get("UNITNAME", "")).strip(),
                "day": day,
                "day_name": str(row["WDAY"]).strip(),
                "slot_id": slot_id,
                "time_raw": str(row["Time"]).strip(),
                "faculty": faculty,
                "room_code": room_code,
                "head_count": int(row["Head Count"]) if pd.notna(row.get("Head Count")) else 0,
            })

        except Exception as e:
            warnings.append({"row": excel_row_num, "type": "PARSE_ERROR", "msg": str(e)})

    # Run the string-based clash detector
    clashes = detect_clashes(cleaned_rows)
    
    return {
        "success": True,
        "total_rows": len(df),
        "cleaned_rows": len(cleaned_rows),
        "warnings": warnings,
        "clashes": clashes,
        "data": cleaned_rows[:50] # Preview first 50 rows
    }