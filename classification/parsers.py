from dataclasses import dataclass
from typing import List, Optional, Dict
import re
import csv
import io
from datetime import datetime, date, timedelta


@dataclass
class Event:
    title: str
    start: Optional[datetime] = None
    end: Optional[datetime] = None
    notes: str = ""
    duration_hours: float = 0.0


def _clean(s: str) -> str:
    if s is None:
        return ""
    return s.replace('\u00A0', ' ').strip().strip('"').strip("'")


def parse_time_str(time_str: str, date_obj: date) -> Optional[datetime]:
    """Parse short human time strings like '9:00 AM', '14:30', '9 AM'."""
    if not time_str:
        return None
    ts = time_str.strip().replace('.', '')
    # Regex to capture hour, optional minute, optional am/pm
    m = re.search(r'(?P<hour>\d{1,2})(?::(?P<minute>\d{2}))?\s*(?P<ampm>AM|PM|am|pm)?', ts)
    if not m:
        return None
    hour = int(m.group('hour'))
    minute = int(m.group('minute') or 0)
    ampm = m.group('ampm')
    if ampm:
        ampm = ampm.lower()
        if ampm == 'am' and hour == 12:
            hour = 0
        elif ampm == 'pm' and hour != 12:
            hour += 12
    # Bound hour
    hour = hour % 24
    try:
        return datetime(year=date_obj.year, month=date_obj.month, day=date_obj.day, hour=hour, minute=minute)
    except Exception:
        return None


def parse_duration_hours(duration_str: str) -> Optional[float]:
    """Parse duration text like '30m', '1h', '1h 30m', or '1.5h'."""
    if not duration_str:
        return None
    raw = duration_str.strip().lower()
    if not raw or raw == "---":
        return None

    minute_match = re.fullmatch(r'(\d+(?:\.\d+)?)\s*m', raw)
    if minute_match:
        return round(float(minute_match.group(1)) / 60.0, 2)

    hour_match = re.fullmatch(r'(\d+(?:\.\d+)?)\s*h', raw)
    if hour_match:
        return round(float(hour_match.group(1)), 2)

    hour_minute_match = re.fullmatch(r'(\d+(?:\.\d+)?)\s*h\s+(\d+(?:\.\d+)?)\s*m', raw)
    if hour_minute_match:
        hours = float(hour_minute_match.group(1))
        minutes = float(hour_minute_match.group(2))
        return round(hours + (minutes / 60.0), 2)

    return None


def parse_agenda(markdown_text: str, date_str: str) -> List[Dict]:
    """Parse an agenda markdown document and return a list of event dicts.

    The parser looks for two common structures produced by `sync_daily_notes.py`:
    - The Calendar table under '## 📅 Calendar' (rows like `| 9:00 AM | Meeting name | link |`)
    - Meeting notes headings like `### 9:00 AM — Meeting name` with body text

    Returns a list of dicts: {'title', 'start', 'end', 'duration_hours', 'notes'}
    """
    d = date.fromisoformat(date_str)
    events: List[Event] = []

    text = markdown_text or ""

    # 1) Meeting notes (detailed stubs)
    # Use explicit alternation for dash characters to avoid regex range parsing issues
    note_pattern = re.compile(r'^(?:###)\s*(?P<time>\d{1,2}(?::\d{2})?\s*(?:AM|PM|am|pm)?)\s*(?:—|-|–)\s*(?P<title>.+)$', re.MULTILINE)
    notes_positions = []
    for m in note_pattern.finditer(text):
        start_idx = m.start()
        notes_positions.append((start_idx, m))

    # Extract note bodies
    for idx, (pos, m) in enumerate(notes_positions):
        time_txt = m.group('time')
        title = _clean(m.group('title'))
        body_start = m.end()
        body_end = notes_positions[idx + 1][0] if idx + 1 < len(notes_positions) else len(text)
        body = text[body_start:body_end].strip()
        ev = Event(title=title)
        ev.start = parse_time_str(time_txt, d)
        ev.notes = body
        events.append(ev)

    # 2) Calendar table rows under Calendar heading
    cal_head = re.search(r'^##\s*.*Calendar', text, re.IGNORECASE | re.MULTILINE)
    if cal_head:
        tail = text[cal_head.end():]
        # Grab contiguous table rows that start with |
        table_lines = []
        for line in tail.splitlines():
            if line.strip().startswith('|'):
                table_lines.append(line)
            elif table_lines:
                break
        for row in table_lines:
            # split on '|' and ignore first/last empty cells
            parts = [p.strip() for p in row.split('|')[1:-1]]
            if not parts:
                continue
            time_cell = parts[0] if len(parts) > 0 else ''
            if len(parts) >= 4:
                duration_cell = parts[1]
                title_cell = parts[2]
            else:
                duration_cell = ''
                title_cell = parts[1] if len(parts) > 1 else ''
            title = _clean(title_cell)
            time_txt = time_cell
            # time range?
            span = re.split(r'\s*(?:-|–|—|to)\s*', time_txt)
            if len(span) == 2:
                start = parse_time_str(span[0], d)
                end = parse_time_str(span[1], d)
            else:
                start = parse_time_str(time_txt, d)
                end = None
            duration_hours = parse_duration_hours(duration_cell)
            if start and end is None and duration_hours and duration_hours > 0:
                end = start + timedelta(hours=duration_hours)

            # Skip duplicates (match by title and start if present)
            dup = False
            for e in events:
                if e.title.lower() == title.lower() and (not start or not e.start or abs((e.start - start).total_seconds()) < 60):
                    dup = True
                    if not e.start and start:
                        e.start = start
                    if end:
                        e.end = end
                    break
            if dup:
                continue

            ev = Event(title=title, start=start, end=end)
            if duration_hours is not None:
                ev.duration_hours = duration_hours
            events.append(ev)

    # 3) Compute end times/durations when missing (use next event start or default 60 minutes)
    events = [e for e in events if e.start is not None]
    events.sort(key=lambda x: x.start)
    for i, e in enumerate(events):
        if e.end is None:
            if i + 1 < len(events) and events[i + 1].start > e.start:
                e.end = events[i + 1].start
            else:
                e.end = e.start + timedelta(minutes=60)
        if e.end <= e.start:
            e.end = e.start + timedelta(minutes=60)
        computed_hours = round((e.end - e.start).total_seconds() / 3600.0, 2)
        if e.duration_hours and e.duration_hours > 0:
            e.duration_hours = round(e.duration_hours, 2)
        else:
            e.duration_hours = computed_hours

    # Convert to serializable dicts
    out = []
    for e in events:
        out.append({
            'title': e.title,
            'start': e.start.isoformat(),
            'end': e.end.isoformat() if e.end else None,
            'duration_hours': e.duration_hours,
            'notes': e.notes,
        })
    return out


def parse_clarity_csv(csv_text: str) -> List[Dict]:
    """Parse the Clarity CSV dump into a flat list of task definitions.

    Returns list of {'project': str, 'task_name': str, 'task_code': str}
    """
    lines = (csv_text or '').splitlines()
    clarity_defs = []
    current_project = ''
    code_re = re.compile(r'(?P<name>.*?)\s*\((?P<code>(?:TSK\d+|PRJ-\d+))\)')
    for raw in lines:
        line = _clean(raw)
        if not line:
            continue
        m = code_re.search(line)
        if not m:
            continue
        name = m.group('name').strip()
        code = m.group('code').strip()
        if code.startswith('PRJ-'):
            current_project = name
            continue
        # TSK code -> task definition
        if code.startswith('TSK'):
            clarity_defs.append({
                'project': current_project,
                'task_name': name,
                'task_code': code,
            })
    return clarity_defs


def parse_corrections_csv(csv_text: str) -> List[Dict]:
    """Parse a user-maintained corrections CSV.

    Expected headers include:
    - source_event (required)
    - project, task_name, task_code (required)
    - date (optional, YYYY-MM-DD)
    - hours (optional; ignored by classifier overrides)
    """
    if not (csv_text or "").strip():
        return []

    reader = csv.DictReader(io.StringIO(csv_text))
    required = {"source_event", "project", "task_name", "task_code"}
    headers = {h.strip().lower() for h in (reader.fieldnames or []) if h}
    if not required.issubset(headers):
        missing = sorted(required - headers)
        raise ValueError(f"Corrections CSV missing required columns: {missing}")

    out: List[Dict] = []
    for row in reader:
        normalized = {str(k).strip().lower(): (v or "").strip() for k, v in row.items() if k is not None}
        source_event = normalized.get("source_event", "")
        task_code = normalized.get("task_code", "")
        if not source_event or not task_code:
            continue
        out.append({
            "date": normalized.get("date", ""),
            "source_event": source_event,
            "project": normalized.get("project", ""),
            "task_name": normalized.get("task_name", ""),
            "task_code": task_code,
        })
    return out
