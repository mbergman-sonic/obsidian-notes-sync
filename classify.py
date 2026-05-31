#!/usr/bin/env python3
"""CLI entrypoint for the Clarity classification skill.

Usage:
  python classify.py --date YYYY-MM-DD [--vault-path PATH] [--clarity-csv PATH] [--corrections-csv PATH] [--append]
  python classify.py --start-date YYYY-MM-DD --end-date YYYY-MM-DD [--vault-path PATH] [--clarity-csv PATH] [--corrections-csv PATH] [--append]
"""
import argparse
import os
from pathlib import Path
import json
from datetime import datetime, timedelta
import re
from dotenv import load_dotenv
from classification import classify_text, format_summary_markdown, append_summary_to_file


def find_agenda_path(date_str: str, vault_path: Path) -> Path:
    candidates = [
        vault_path / "Work" / "Sonic" / "Daily" / f"{date_str}_Agenda.md",
        Path(f"{date_str}_Agenda.md"),
        Path(f"{date_str}.md"),
    ]
    for p in candidates:
        if p.exists():
            return p
    raise FileNotFoundError(f"Could not locate agenda file for {date_str}; tried: {candidates}")


def date_range_inclusive(start_date: str, end_date: str):
    start = datetime.strptime(start_date, "%Y-%m-%d").date()
    end = datetime.strptime(end_date, "%Y-%m-%d").date()
    if end < start:
        raise ValueError(f"end-date ({end_date}) must be on or after start-date ({start_date})")
    current = start
    while current <= end:
        yield current.isoformat()
        current += timedelta(days=1)


def main():
    load_dotenv()

    parser = argparse.ArgumentParser(description='Classify a daily agenda to Clarity task codes')
    parser.add_argument('--date', required=False, help='Single date to classify (YYYY-MM-DD)')
    parser.add_argument('--start-date', required=False, help='Start date for range classification (YYYY-MM-DD)')
    parser.add_argument('--end-date', required=False, help='End date for range classification (YYYY-MM-DD)')
    parser.add_argument('--vault-path', required=False, help='Obsidian vault root (overrides OBSIDIAN_VAULT_PATH)')
    parser.add_argument('--clarity-csv', required=False, help='Path to Clarity-definitions.csv')
    parser.add_argument(
        '--corrections-csv',
        required=False,
        help='Path to corrections CSV (defaults to resources/clarity-corrections.csv if present)',
    )
    parser.add_argument('--append', dest='append', action='store_true', help='Append human-readable summary to the agenda file')
    parser.add_argument('--no-append', dest='append', action='store_false', help='Do not append summary to the agenda file')
    parser.set_defaults(append=False)
    parser.add_argument(
        '--clean-legacy-clarity',
        action='store_true',
        help='Remove legacy appended "Clarity Summary (auto-generated)" blocks from agenda files before processing',
    )
    parser.add_argument('--output-json', required=False, help='Write JSON output to file')
    parser.add_argument(
        '--output-md',
        action='store_true',
        help='Write a human-readable markdown summary per processed day to the Clarity Processing folder',
    )

    args = parser.parse_args()

    using_single = bool(args.date)
    using_range = bool(args.start_date or args.end_date)

    if using_single and using_range:
        raise ValueError("Use either --date or --start-date/--end-date, not both.")
    if not using_single and not using_range:
        raise ValueError("Provide either --date or --start-date/--end-date.")
    if using_range and not (args.start_date and args.end_date):
        raise ValueError("Both --start-date and --end-date are required for range classification.")

    vault_env = os.getenv('OBSIDIAN_VAULT_PATH')
    if args.vault_path:
        vault = Path(args.vault_path)
    elif vault_env:
        vault = Path(vault_env)
    else:
        raise ValueError(
            "Vault path is required. Provide --vault-path or set OBSIDIAN_VAULT_PATH in .env."
        )
    print(f"Using vault path: {vault}")
    clarity_csv_path = Path(args.clarity_csv) if args.clarity_csv else Path('resources') / 'Clarity-definitions.csv'
    if not clarity_csv_path.exists():
        raise FileNotFoundError(f"Clarity CSV not found at {clarity_csv_path}")
    corrections_csv_path = Path(args.corrections_csv) if args.corrections_csv else Path('resources') / 'clarity-corrections.csv'

    clarity_text = clarity_csv_path.read_text(encoding='utf-8')
    corrections_text = None
    if corrections_csv_path.exists():
        corrections_text = corrections_csv_path.read_text(encoding='utf-8')
        print(f"Using corrections CSV: {corrections_csv_path}")
    elif args.corrections_csv:
        raise FileNotFoundError(f"Corrections CSV not found at {corrections_csv_path}")
    else:
        print("No corrections CSV found; running with base rules only.")
    dates_to_run = [args.date] if using_single else list(date_range_inclusive(args.start_date, args.end_date))

    day_summaries = []
    skipped_dates = []
    clarity_processing_dir = vault / "Work" / "Sonic" / "Clarity Processing"
    clarity_processing_dir.mkdir(parents=True, exist_ok=True)

    def _write_day_artifacts(day_summary: dict):
        day = day_summary.get('date')
        if not day:
            return
        json_path = clarity_processing_dir / f"{day}_clarity.json"
        json_path.write_text(json.dumps(day_summary, indent=2), encoding='utf-8')
        print(f"Wrote daily Clarity JSON to {json_path}")
        if args.output_md:
            md_path = clarity_processing_dir / f"{day}_clarity.md"
            md_path.write_text(format_summary_markdown(day_summary), encoding='utf-8')
            print(f"Wrote daily Clarity Markdown to {md_path}")

    for date_str in dates_to_run:
        try:
            agenda_path = find_agenda_path(date_str, vault)
        except FileNotFoundError:
            skipped_dates.append(date_str)
            continue
        print(f"Using agenda file for {date_str}: {agenda_path}")

        agenda_text = agenda_path.read_text(encoding='utf-8')
        if args.clean_legacy_clarity:
            cleaned_text = re.sub(
                r'\n## Clarity Summary \(auto-generated\)\n.*?(?=\n## |\Z)',
                '\n',
                agenda_text,
                flags=re.S,
            ).rstrip()
            if cleaned_text != agenda_text.rstrip():
                agenda_path.write_text(cleaned_text + '\n', encoding='utf-8')
                agenda_text = cleaned_text
                print(f"Removed legacy Clarity summary block(s) from {agenda_path}")

        summary = classify_text(agenda_text, clarity_text, date_str, corrections_csv_text=corrections_text)
        day_summaries.append(summary)
        _write_day_artifacts(summary)

        # Append human-readable markdown to agenda file
        if args.append:
            md = format_summary_markdown(summary)
            append_summary_to_file(str(agenda_path), md)
            print(f"Appended Clarity summary to {agenda_path}")

    if using_single:
        result = day_summaries[0] if day_summaries else {'date': args.date, 'entries': [], 'event_count': 0}
    else:
        result = {
            'start_date': args.start_date,
            'end_date': args.end_date,
            'day_count': len(day_summaries),
            'skipped_dates': skipped_dates,
            'days': day_summaries,
        }

    # Print JSON to stdout
    print(json.dumps(result, indent=2))

    # Optionally write JSON to file
    if args.output_json:
        Path(args.output_json).write_text(json.dumps(result, indent=2), encoding='utf-8')


if __name__ == '__main__':
    main()
