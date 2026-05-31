"""Classification package entry points.

Exports:
- `classify_text(agenda_text: str, clarity_csv_text: str, date_str: str, corrections_csv_text: Optional[str]=None) -> dict` (pure)
- `classify_day(date_str: str, vault_path: Optional[str]=None, clarity_csv_path: Optional[str]=None) -> dict` (convenience wrapper)
- `format_summary_markdown(summary_dict: dict) -> str`
- `append_summary_to_file(path: str, markdown: str) -> None` (side-effect helper)
"""
from .parsers import parse_agenda, parse_clarity_csv, parse_corrections_csv
from .classifier import classify_events
from .formatters import format_summary_markdown
from pathlib import Path
import os
from typing import Optional

DEFAULT_CLARITY_CSV = os.path.join("resources", "Clarity-definitions.csv")


def classify_text(
    agenda_text: str,
    clarity_csv_text: str,
    date_str: str,
    llm_classifier=None,
    corrections_csv_text: Optional[str] = None
) -> dict:
    """Pure classification function. No side-effects.

    Params:
      - agenda_text: raw markdown of the day's agenda
      - clarity_csv_text: raw CSV text of clarity definitions
      - date_str: ISO date 'YYYY-MM-DD'
      - llm_classifier: optional callable(event)->(project, task_name, task_code)
      - corrections_csv_text: optional raw corrections CSV used for exact source_event overrides

    Returns structured dict (see project README / user's spec).
    """
    clarity_defs = parse_clarity_csv(clarity_csv_text)
    corrections = parse_corrections_csv(corrections_csv_text) if corrections_csv_text is not None else []
    events = parse_agenda(agenda_text, date_str)
    result = classify_events(
        events,
        clarity_defs,
        date_str,
        llm_classifier=llm_classifier,
        corrections=corrections,
    )
    return result


def _read_text_file(path: Path) -> str:
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()


def classify_day(date_str: str, vault_path: Optional[str] = None, clarity_csv_path: Optional[str] = None) -> dict:
    """Convenience wrapper that reads the agenda file and clarity CSV, then calls `classify_text`.

    This wrapper performs IO; the core classifier (`classify_text`) remains pure.
    """
    # determine vault path
    vault = Path(vault_path) if vault_path else Path(os.getenv('OBSIDIAN_VAULT_PATH', '.'))

    # Default sonic path used by sync_daily_notes.py / legacy spec
    agenda_candidates = [
        vault / "Work" / "Sonic" / "Daily" / f"{date_str}_Agenda.md",
        Path(f"{date_str}_Agenda.md"),
        Path(f"{date_str}.md"),
    ]

    agenda_path = None
    for p in agenda_candidates:
        if p.exists():
            agenda_path = p
            break

    if not agenda_path:
        raise FileNotFoundError(f"Could not locate agenda file for {date_str}; tried: {agenda_candidates}")

    # clarity CSV
    csv_path = Path(clarity_csv_path) if clarity_csv_path else Path(DEFAULT_CLARITY_CSV)
    if not csv_path.exists():
        raise FileNotFoundError(f"Could not locate Clarity CSV at {csv_path}")

    agenda_text = _read_text_file(agenda_path)
    clarity_csv_text = _read_text_file(csv_path)

    return classify_text(agenda_text, clarity_csv_text, date_str)


def append_summary_to_file(path: str, markdown: str) -> None:
    """Append the given markdown to the end of `path` (creates file if missing)."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, 'a', encoding='utf-8') as f:
        f.write("\n\n")
        f.write(markdown)


__all__ = [
    "classify_text",
    "classify_day",
    "format_summary_markdown",
    "append_summary_to_file",
]
