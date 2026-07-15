#!/usr/bin/env python3
"""Generate daily and weekly recap markdown from Obsidian agenda notes."""

import argparse
import os
import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import List

try:
    from dotenv import load_dotenv
except ImportError:
    def load_dotenv(*args, **kwargs):
        return False


@dataclass
class DailyRecap:
    date: str
    shipped: List[str] = field(default_factory=list)
    delegated: List[str] = field(default_factory=list)
    gabe_updates: List[str] = field(default_factory=list)
    carry_forward: List[str] = field(default_factory=list)
    blockers: List[str] = field(default_factory=list)
    completed_tasks: List[str] = field(default_factory=list)


def split_bullets(text: str) -> List[str]:
    lines = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        line = re.sub(r'^[-*+]\s*', '', line)
        lines.append(line)
    return lines


def extract_section(text: str, heading: str) -> str:
    pattern = rf'^##\s+{re.escape(heading)}\s*\n(.*?)(?=^##\s+|\Z)'
    match = re.search(pattern, text, flags=re.MULTILINE | re.DOTALL)
    return match.group(1).strip() if match else ''


def extract_prompt_answer(section_text: str, prompt: str) -> List[str]:
    escaped = re.escape(prompt)
    pattern = rf'\*\*{escaped}\*\*\s*\n(.*?)(?=\n\*\*|\Z)'
    match = re.search(pattern, section_text, flags=re.DOTALL)
    if not match:
        return []
    answer = match.group(1).strip()
    if not answer:
        return []
    return split_bullets(answer)


def extract_blockers(section_text: str) -> List[str]:
    blockers = []
    for line in section_text.splitlines():
        stripped = line.strip()
        if not stripped.startswith('|'):
            continue
        columns = [part.strip() for part in stripped.strip('|').split('|')]
        if len(columns) != 4:
            continue
        if columns[0].lower() == 'blocker' or set(''.join(columns)) <= {'-', ' '}:
            continue
        if not any(columns):
            continue
        blockers.append(' | '.join(value for value in columns if value))
    return blockers


def extract_completed_tasks(text: str) -> List[str]:
    tasks = []
    for line in text.splitlines():
        match = re.match(r'^\s*[-*+]\s*\[[xX]\]\s*(.+?)\s*(?:<!--.*-->)?\s*$', line)
        if not match:
            continue
        task = re.sub(r'\s*[🔴🟠🟡]\s*$', '', match.group(1)).strip()
        task = re.sub(r'\s*\(due:\s*\d{4}-\d{2}-\d{2}\)\s*$', '', task).strip()
        if task:
            tasks.append(task)
    return tasks


def load_agenda(date_str: str, vault_path: Path) -> str:
    agenda_path = vault_path / 'Work' / 'Sonic' / 'Daily' / f'{date_str}_Agenda.md'
    if not agenda_path.exists():
        raise FileNotFoundError(f'Agenda not found: {agenda_path}')
    return agenda_path.read_text(encoding='utf-8')


def build_daily_recap(date_str: str, vault_path: Path) -> DailyRecap:
    agenda = load_agenda(date_str, vault_path)
    end_of_day = extract_section(agenda, '📤 End of day')
    blockers_section = extract_section(agenda, '🚦 Blockers & next steps')

    shipped = extract_prompt_answer(end_of_day, 'What I shipped or moved forward today:')
    delegated = extract_prompt_answer(end_of_day, 'What I would have held but delegated instead:')
    gabe_updates = extract_prompt_answer(end_of_day, 'One thing Gabe should know from today:')
    carry_forward = extract_prompt_answer(end_of_day, 'Anything to carry into tomorrow:')
    completed_tasks = extract_completed_tasks(agenda)

    if not shipped:
        shipped = completed_tasks[:]

    return DailyRecap(
        date=date_str,
        shipped=shipped,
        delegated=delegated,
        gabe_updates=gabe_updates,
        carry_forward=carry_forward,
        blockers=extract_blockers(blockers_section),
        completed_tasks=completed_tasks,
    )


def render_daily_summary(recap: DailyRecap) -> str:
    lines = [f'# {recap.date} Daily Summary', '']

    def add_section(title: str, items: List[str], empty: str):
        lines.append(f'## {title}')
        if items:
            for item in items:
                lines.append(f'- {item}')
        else:
            lines.append(empty)
        lines.append('')

    add_section('Shipped / Moved Forward', recap.shipped, '*No end-of-day summary captured yet.*')
    add_section('Delegated', recap.delegated, '*No delegation notes captured.*')
    add_section('Gabe Should Know', recap.gabe_updates, '*Nothing explicitly flagged for Gabe yet.*')
    add_section('Blockers', recap.blockers, '*No blockers captured.*')
    add_section('Carry Forward', recap.carry_forward, '*Nothing queued for tomorrow.*')

    if recap.completed_tasks:
        lines.append('## Completed Tasks')
        for task in recap.completed_tasks:
            lines.append(f'- {task}')
        lines.append('')

    return '\n'.join(lines).rstrip() + '\n'


def render_weekly_summary(recaps: List[DailyRecap], end_date: str) -> str:
    lines = [f'# Weekly Summary for Gabe ({end_date})', '']

    def aggregate(attr: str) -> List[str]:
        values = []
        for recap in recaps:
            values.extend(getattr(recap, attr))
        deduped = []
        seen = set()
        for value in values:
            normalized = value.strip().lower()
            if not normalized or normalized in seen:
                continue
            seen.add(normalized)
            deduped.append(value)
        return deduped

    sections = [
        ('Highlights', aggregate('shipped'), '*No shipped highlights captured this week.*'),
        ('Delegated', aggregate('delegated'), '*No delegation notes captured this week.*'),
        ('Risks / Blockers', aggregate('blockers'), '*No blockers captured this week.*'),
        ('Carry Into Next Week', aggregate('carry_forward'), '*Nothing captured to carry forward.*'),
        ('Gabe FYIs', aggregate('gabe_updates'), '*No explicit FYIs captured for Gabe this week.*'),
    ]

    for title, items, empty in sections:
        lines.append(f'## {title}')
        if items:
            for item in items:
                lines.append(f'- {item}')
        else:
            lines.append(empty)
        lines.append('')

    lines.append('## Daily References')
    for recap in recaps:
        lines.append(
            f'- {recap.date}: {len(recap.shipped)} shipped, '
            f'{len(recap.blockers)} blockers, {len(recap.carry_forward)} carry-forward items'
        )
    lines.append('')

    return '\n'.join(lines).rstrip() + '\n'


def write_summary(vault_path: Path, filename: str, content: str) -> Path:
    output_dir = vault_path / 'Work' / 'Sonic' / 'Summaries'
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / filename
    output_path.write_text(content, encoding='utf-8')
    return output_path


def monday_for(date_str: str):
    day = datetime.strptime(date_str, '%Y-%m-%d').date()
    return day - timedelta(days=day.weekday())


def main():
    load_dotenv()

    parser = argparse.ArgumentParser(description='Generate daily or weekly recap markdown from agenda notes')
    parser.add_argument('--mode', choices=['daily', 'weekly'], required=True)
    parser.add_argument('--date', help='Target date in YYYY-MM-DD format (defaults to today)')
    parser.add_argument('--vault-path', help='Obsidian vault root (overrides OBSIDIAN_VAULT_PATH)')
    args = parser.parse_args()

    date_str = args.date or datetime.now().date().isoformat()
    vault_env = os.getenv('OBSIDIAN_VAULT_PATH')
    vault_path = Path(args.vault_path or vault_env or '')
    if not str(vault_path):
        raise ValueError('Vault path is required. Provide --vault-path or set OBSIDIAN_VAULT_PATH in .env.')

    if args.mode == 'daily':
        recap = build_daily_recap(date_str, vault_path)
        content = render_daily_summary(recap)
        output_path = write_summary(vault_path, f'{date_str}_daily-summary.md', content)
        print(output_path)
        return

    start_day = monday_for(date_str)
    end_day = datetime.strptime(date_str, '%Y-%m-%d').date()
    recaps = []
    current = start_day
    while current <= end_day:
        day_str = current.isoformat()
        try:
            recaps.append(build_daily_recap(day_str, vault_path))
        except FileNotFoundError:
            pass
        current += timedelta(days=1)

    content = render_weekly_summary(recaps, date_str)
    output_path = write_summary(vault_path, f'{date_str}_gabe-weekly-summary.md', content)
    print(output_path)


if __name__ == '__main__':
    main()
