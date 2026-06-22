import pandas as pd
import re
from typing import Dict, List, Any

# Normalization maps based on the PDF and Excel data
DAY_MAP = {
    'MON': 'MON', 'MONDAY': 'MON',
    'TUE': 'TUE', 'TUESDAY': 'TUE',
    'WED': 'WED', 'WEDNESDAY': 'WED',
    'THU': 'THU', 'THURSDAY': 'THU',
    'FRI': 'FRI', 'FRIDAY': 'FRI',
    'SAT': 'SAT', 'SATURDAY': 'SAT',
}

TIME_SLOT_MAP = {
    "9:00AM - 10:55AM": 1, "09:00AM - 10:55AM": 1, "9:00AM-10:55AM": 1, "9:00-10:55": 1,
    "11:05AM - 1:00PM": 2, "11:05AM-1:00PM": 2, "11:05-1:00": 2, "11:00AM - 12:55PM": 2,
    "2:00PM - 3:55PM": 3, "2:00PM-3:55PM": 3, "2:00-3:55": 3,
    "4:05PM - 6:00PM": 4, "4:05-6:00": 4, "4:05PM-6:00PM": 4,
    "5:45PM - 8:00PM": 5, 
}

def normalize_time_slot(time_str: str) -> int | None:
    if not time_str or pd.isna(time_str): return None
    time_str = str(time_str).strip().upper().replace('–', '-').replace(' ', '')
    return TIME_SLOT_MAP.get(time_str)

def normalize_day(day_str: str) -> str | None:
    if not day_str or pd.isna(day_str): return None
    return DAY_MAP.get(str(day_str).strip().upper())

def parse_draft_timetable(file_path: str) -> Dict[str, Any]:
    """Parses the 'Time Table' sheet to detect clashes and extract scheduling data."""
    try:
        df = pd.read_excel(file_path, sheet_name='Time Table')
    except Exception as e:
        return {"error": f"Could not read 'Time Table' sheet: {str(e)}"}

    df.columns = [str(c).strip() for c in df.columns]
    df = df.dropna(subset=['BATCHCODE', 'WDAY', 'Time'])
    
    cleaned_rows = []
    warnings = []
    clashes = {"room": [], "lecturer": [], "student_group": []}
    
    room_bookings = {}
    lecturer_bookings = {}
    batch_bookings = {}

    for index, row in df.iterrows():
        batch_code = str(row.get('BATCHCODE')).strip()
        unit_code = str(row.get('UNITCODE')).strip()
        unit_name = str(row.get('UNITNAME')).strip()
        room_code = str(row.get('ROOMCODE')).strip() if not pd.isna(row.get('ROOMCODE')) else 'UNASSIGNED'
        faculty = str(row.get('Faculty')).strip() if not pd.isna(row.get('Faculty')) else 'UNKNOWN'
        
        day = normalize_day(row.get('WDAY'))
        slot = normalize_time_slot(row.get('Time'))
        
        if not day or not slot:
            warnings.append(f"Row {index + 2}: Invalid Day or Time format.")
            continue
            
        cleaned_rows.append({
            "row": index + 2, "batch_code": batch_code, "unit_code": unit_code,
            "unit_name": unit_name, "room_code": room_code, "faculty": faculty,
            "day": day, "slot": slot
        })
        
        # Clash Detection
        room_key = (day, slot, room_code)
        if room_key in room_bookings and room_code != 'UNASSIGNED':
            clashes["room"].append(f"Room {room_code} double booked on {day} Slot {slot}")
        else:
            room_bookings[room_key] = batch_code
            
        lec_key = (day, slot, faculty)
        if lec_key in lecturer_bookings and faculty not in ['UNKNOWN', 'X']:
            clashes["lecturer"].append(f"Lecturer {faculty} double booked on {day} Slot {slot}")
        else:
            lecturer_bookings[lec_key] = batch_code
            
        batch_key = (day, slot, batch_code)
        if batch_key in batch_bookings:
            clashes["student_group"].append(f"Batch {batch_code} double booked on {day} Slot {slot}")
        else:
            batch_bookings[batch_key] = room_code

    return {
        "total_rows_parsed": len(cleaned_rows),
        "warnings": warnings,
        "clashes": clashes,
        "data": cleaned_rows
    }