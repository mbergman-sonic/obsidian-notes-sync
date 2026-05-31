from typing import List, Dict, Optional, Callable
import re

RULE_MATCH_CONFIDENCE = 0.95

# Ordered, easy-to-extend rule list. Add new rules at the end unless they need
# higher precedence than existing rules.
CLASSIFICATION_RULES: List[Dict] = [
    {
        'name': 'training_bootcamp',
        'keywords': ['bootcamp'],
        'targets': ['training'],
    },
    {
        'name': 'internal_1on1',
        'keywords': ['1 on 1', '1:1', 'one on one'],
        'targets': ['internal meetings', 'internal'],
    },
    {
        'name': 'internal_cab',
        'keywords': ['cab'],
        'targets': ['internal meetings', 'internal'],
    },
    {
        'name': 'turbo_project',
        'keywords': ['turbo'],
        'targets': ['turbo'],
    },
    {
        'name': 'data_engineering_keywords',
        'keywords': ['experian', 'sap', 'data'],
        'targets': ['data engineering', 'data'],
    },
    {
        'name': 'data_analysis_keywords',
        'keywords': ['review', 'metrics'],
        'targets': ['data analysis', 'analysis'],
    },
    {
        'name': 'project_management_keywords',
        'keywords': ['planning', 'catch up'],
        'targets': ['project management', 'management'],
    },
]


def _normalize(s: str) -> str:
    return (s or '').lower()


def _token_set(s: str):
    return set(re.findall(r"\w+", _normalize(s)))


def _score_match(text: str, clarity_def: Dict) -> int:
    """Return a heuristic score for how well a clarity_def matches event text."""
    score = 0
    t = _normalize(text)
    task = _normalize(clarity_def.get('task_name', ''))
    proj = _normalize(clarity_def.get('project', ''))

    # High value for direct substring matches
    if task and task in t:
        score += 100
    if proj and proj in t:
        score += 50

    # Token overlap
    task_tokens = _token_set(task)
    text_tokens = _token_set(t)
    overlap = len(task_tokens & text_tokens)
    score += overlap * 10

    # If the event text includes parts of the project name
    proj_tokens = _token_set(proj)
    score += len(proj_tokens & text_tokens) * 5

    return score


def _find_by_targets(clarity_defs: List[Dict], targets: List[str]) -> Optional[Dict]:
    normalized_targets = [_normalize(t) for t in (targets or [])]
    for d in (clarity_defs or []):
        task = _normalize(d.get('task_name', ''))
        proj = _normalize(d.get('project', ''))
        combined = f'{task} {proj}'
        if any(t and t in combined for t in normalized_targets):
            return d
    return None


def _classify_by_rules(text: str, clarity_defs: List[Dict]) -> Optional[Dict]:
    normalized_text = _normalize(text)
    for rule in CLASSIFICATION_RULES:
        keywords = [_normalize(k) for k in rule.get('keywords', [])]
        if any(k and k in normalized_text for k in keywords):
            matched = _find_by_targets(clarity_defs, rule.get('targets', []))
            if matched:
                return {
                    'project': matched.get('project', ''),
                    'task_name': matched.get('task_name', ''),
                    'task_code': matched.get('task_code', ''),
                    'confidence': RULE_MATCH_CONFIDENCE,
                    'rule_name': rule.get('name', ''),
                }
    return None


def _internal_default_def(clarity_defs: List[Dict]) -> Dict:
    for d in (clarity_defs or []):
        if 'internal' in _normalize(d.get('task_name', '')):
            return d
    return {'project': 'Internal', 'task_name': 'Internal Meetings', 'task_code': 'INTERNAL'}


def _normalize_confidence(score: int) -> float:
    # Bound fallback confidence to a practical range.
    if score <= 0:
        return 0.5
    return round(min(0.85, 0.5 + (score / 200.0)), 2)


def _match_correction(event: Dict, date_str: str, corrections: Optional[List[Dict]]) -> Optional[Dict]:
    if not corrections:
        return None
    title = _normalize(event.get('title', '')).strip()
    for c in corrections:
        correction_date = (c.get('date') or '').strip()
        if correction_date and correction_date != date_str:
            continue
        if _normalize(c.get('source_event', '')).strip() == title:
            return {
                'task_name': c.get('task_name', ''),
                'task_code': c.get('task_code', ''),
                'project': c.get('project', ''),
                'confidence': 1.0,
            }
    return None


def classify_event(
    event: Dict,
    clarity_defs: List[Dict],
    date_str: str,
    llm_classifier: Optional[Callable] = None,
    corrections: Optional[List[Dict]] = None
) -> Dict:
    """Classify one event to a Clarity task with confidence."""
    defs = clarity_defs or []
    title = event.get('title', '')
    notes = event.get('notes', '')
    text = f'{title} {notes}'.strip()

    # 0) User corrections override all automated logic.
    corrected = _match_correction(event, date_str, corrections)
    if corrected:
        return corrected

    # 1) Deterministic rule-first mapping.
    rule_assigned = _classify_by_rules(text, defs)
    if rule_assigned:
        return {
            'task_name': rule_assigned.get('task_name', ''),
            'task_code': rule_assigned.get('task_code', ''),
            'project': rule_assigned.get('project', ''),
            'confidence': rule_assigned.get('confidence', RULE_MATCH_CONFIDENCE),
        }

    # 2) Fallback token scoring.
    best = None
    best_score = 0
    for d in defs:
        s = _score_match(text, d)
        if s > best_score:
            best_score = s
            best = d

    if best_score > 0 and best:
        return {
            'task_name': best.get('task_name', ''),
            'task_code': best.get('task_code', ''),
            'project': best.get('project', ''),
            'confidence': _normalize_confidence(best_score),
        }

    # 3) Optional LLM hook only when deterministic methods cannot classify.
    if llm_classifier:
        try:
            proj, task_name, task_code = llm_classifier(event)
            if task_code:
                return {
                    'task_name': task_name or '',
                    'task_code': task_code or '',
                    'project': proj or '',
                    'confidence': 0.7,
                }
        except Exception:
            pass

    # 4) Default assignment.
    internal_def = _internal_default_def(defs)
    return {
        'task_name': internal_def.get('task_name', 'Internal Meetings'),
        'task_code': internal_def.get('task_code', 'INTERNAL'),
        'project': internal_def.get('project', 'Internal'),
        'confidence': 0.5,
    }


def classify_events(
    events: List[Dict],
    clarity_defs: List[Dict],
    date_str: str,
    llm_classifier: Optional[Callable] = None,
    corrections: Optional[List[Dict]] = None
) -> Dict:
    """Classify a list of parsed events against clarity definitions.

    Returns a structured dict with one entry per source event.
    """
    entries: List[Dict] = []
    for ev in events:
        title = ev.get('title', '')
        duration = float(ev.get('duration_hours') or 0.0)
        assigned = classify_event(
            ev,
            clarity_defs,
            date_str,
            llm_classifier=llm_classifier,
            corrections=corrections,
        )
        entries.append({
            'task_name': assigned.get('task_name', ''),
            'task_code': assigned.get('task_code', ''),
            'project': assigned.get('project', ''),
            'hours': round(duration, 2),
            'source_event': title
        })

    entries.sort(key=lambda x: x['hours'], reverse=True)

    return {
        'date': date_str,
        'entries': entries,
        'event_count': len(events)
    }
