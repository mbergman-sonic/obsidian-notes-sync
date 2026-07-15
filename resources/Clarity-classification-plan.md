# Clarity classification — plan

Date: 2026-05-28

## Purpose

Add a hybrid, rule-first `classify_event` function to map agenda events (title + notes) to Clarity task codes (TSK IDs) and provide a confidence score. This file mirrors the agent memory plan so it's visible in the repo for collaborators.

## Requirements (from user)

0. Prioritize these workflow updates before all other plan items:
   - `sync_daily_notes` calendar table must include an event length column.
   - `classify` must reference the calendar table and use event length for assigning time.
   - `classify` must add a checkbox column to the left side of the output table to track whether rows were added to Clarity.
1. Implement `classify_event(event: dict, clarity_defs: list) -> dict` returning:
   - `task_name`, `task_code`, `project`, `confidence`
2. Hybrid approach:
   - Rule-based classification FIRST (high priority)
   - Fallback token/score-based classification if no rule matches
3. Keyword rules (priority order):
   - `bootcamp` → Training
   - `1 on 1`, `1:1`, `one on one` → Internal Meetings
   - `CAB` → Internal Meetings
   - `Turbo` → TURBO project
   - `Experian`, `SAP`, `data` → Data Engineering
   - `review`, `metrics` → Data Analysis
   - `planning`, `catch up` → Project Management
4. Default behavior: if still no match → Internal Meetings
5. Use both `title` + `notes` when classifying (combine them for matching)
6. Prioritize accuracy using the user's consistent patterns (simple keyword rules), not general NLP.

## Implementation plan

0. Implement this ordered pre-work before existing classifier work:
   - Update calendar rendering in `sync_daily_notes.py` to include event duration/length.
   - Update classify input parsing to read calendar table duration and use it as the source of assigned time.
   - Update classify table output to prepend a checkbox column for Clarity completion tracking.
1. Add `classify_event(event, clarity_defs)` to `classification/classifier.py`:
   - Concatenate `title` and `notes` (lowercased) into a single `text` string.
   - Implement keyword rules as an ordered, easy-to-extend dictionary/list structure in code (single place to add new learned patterns).
   - Run keyword rules in the order listed above. For a rule match, search `clarity_defs` for a candidate by looking for task_name/project substrings; return the best match with `confidence=0.95`.
2. Fallback: if no rule match, perform token-overlap scoring across `clarity_defs` (title+notes) and return the best match with a confidence derived from normalized score (e.g., 0.50–0.85).
3. Default: if still no candidate, return the `Internal Meetings` definition (or `INTERNAL`) with `confidence=0.5`.
4. Update `classify_events()` to call `classify_event()` for each event and keep the existing aggregation behavior unchanged.
5. Add unit tests in `tests/test_classifier.py` for the keyword rules and fallback behavior.
6. Run tests (`python -m unittest discover -v`) and iterate until passing.
7. Create a reusable company skill file (`SKILL.md`) that documents how anyone can classify a day's activity list using:
   - Input A: list of daily activities (title + optional notes + optional duration)
   - Input B: CSV export of available Clarity activities/projects
   - Output: structured task-code summary (and optional Markdown table)

## Testing plan (examples)

- Title: `Bootcamp: Python` → expect `Training` task, confidence >= 0.9
- Title: `1:1 with Alice` → expect `Internal Meetings`
- Title: `Turbo: Sprint Planning` → expect `TURBO` project/TSK
- Title or notes contain `Experian` or `SAP` → expect `Data Engineering`-related task
- Notes contain `metrics` → expect `Data Analysis`
- Empty/ambiguous title/notes → default `Internal Meetings`

## Files to modify / add

- `classification/classifier.py` (add `classify_event` and integrate)
- `tests/test_classifier.py` (new tests)
- `resources/skills/clarity-classification/SKILL.md` (new reusable company skill doc)

## Acceptance criteria

- `classify_event` implemented with the keyword rules above
- Unit tests cover all rule paths and fallback behavior
- All tests pass locally
- Shareable `SKILL.md` exists with clear inputs, steps, outputs, and extension guidance for adding new keyword rules

## Current status

- `classify_event`: not-started
- `classify_events()` integration: not-started
- Unit tests: not-started
- Run tests & verify: not-started

## Todo additions

- [ ] Add an ordered keyword-rule dictionary in `classification/classifier.py` that is intentionally easy to extend as new classification patterns are learned.

## Notes / Future

- Keep the `llm_classifier` hook available for optional future use; call it only after deterministic rules/fallbacks if enabled.
- Consider adding logging for traceability (which rule matched, matched term, confidence).
