from typing import Dict


def format_summary_markdown(summary: Dict) -> str:
    """Return a Markdown string summarizing the classification suitable for pasting into Clarity UI."""
    lines = []
    lines.append('## Clarity Summary (auto-generated)')
    lines.append('')

    entries = summary.get('entries', [])
    if not entries:
        lines.append('*No classified entries found.*')
        return '\n'.join(lines)

    # Table header
    lines.append('| Project | Task | Code | Hours | Event |')
    lines.append('|---|---|---:|---:|---|')
    for e in entries:
        proj = e.get('project') or ''
        task = e.get('task_name') or ''
        code = e.get('task_code') or ''
        hours = e.get('hours') or 0.0
        event = e.get('source_event') or ''
        # Escape pipe characters in event text
        event = event.replace('|', '\\|')
        lines.append(f'| {proj} | {task} | {code} | {hours:.2f} | {event} |')

    return '\n'.join(lines)
