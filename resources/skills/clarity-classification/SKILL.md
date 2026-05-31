# Clarity Daily Activity Classification Skill

## Purpose
Convert a person's daily activity list into Clarity-ready, per-event classifications using a deterministic, rule-first classifier and the team's Clarity activity CSV definitions.

## Inputs

1. Daily activities list
- Required fields per activity: `title`
- Optional fields: `notes`, `duration_hours`, optional `start`/`end` timestamps (ISO)
- Accepted sources:
  - Agenda markdown file with calendar/events. Agenda markdown must list events as bullet lines in the form `- HH:MM-HH:MM Title -- optional notes` or provide programmatic JSON as `[{ 'title': '...', 'notes': '...', 'duration_hours': 1.0 }]`. Include examples in `examples/` for reproducibility.
  - JSON-like list passed programmatically (see portability contract)

Duration & time accounting rules:
- If an activity has `duration_hours`, use that numeric value.
- If absent but `start`/`end` timestamps are present, compute `duration = end - start` in hours.
- If neither is available, default to `0.5` hours.
- Round all durations to the nearest `0.25` hour before aggregation.
- If events overlap, keep both durations (do not auto-truncate) unless a repository-specific deduplication rule applies.
- If total hours for a date exceed 24, cap totals at `24` and set top-level flag `hours_adjusted: true` in output.

2. Clarity definitions CSV
- CSV that includes available Clarity project/task definitions.
- Required columns (case-insensitive): `project`, `task_name`, `task_code`.

CSV validation and lifecycle handling:
- Before classification validate CSV headers (case-insensitive) contain `project`, `task_name`, `task_code`.
- If the Clarity CSV cannot be parsed or does not contain the required columns 'project','task_name','task_code' (case-insensitive), abort classification and return JSON: { 'error': 'Invalid Clarity CSV', 'missing_columns': [ ... ] } and exit with non-zero status. Log the full CSV header for debugging.
- Ignore rows marked `inactive` if such a column exists.
- If duplicate `task_code` rows exist, prefer the row where `project` and `task_name` are most complete (non-empty); if duplicates remain, raise an error and abort.

## Output

Return a deterministic structured summary JSON with one entry per input event.

Output JSON schema:
```
{
  'date': 'YYYY-MM-DD',
  'entries': [
    {
      'task_name': string,
      'task_code': string,
      'project': string,
      'hours': number,                 # rounded duration for this event
      'source_event': string
    }
  ],
  'event_count': int,                 # number of input events processed
  'hours_adjusted': bool?             # present if totals were capped at 24
}
```

Example (one-entry):
```json
{
  "date": "2026-05-28",
  "entries": [
    {
      "task_name": "Internal Meetings",
      "task_code": "TSK001172",
      "project": "Internal",
      "hours": 1.0,
      "source_event": "Team Sync"
    }
  ],
  "event_count": 1
}
```

If no events are found for the specified date, return JSON: { 'date': 'YYYY-MM-DD', 'entries': [], 'event_count': 0 } and exit with status 0.

CLI behavior for this repository:
- `python classify.py --date YYYY-MM-DD` processes one day.
- It writes JSON to `Work/Sonic/Clarity Processing/YYYY-MM-DD_clarity.json`.
- With `--output-md`, it also writes `Work/Sonic/Clarity Processing/YYYY-MM-DD_clarity.md`.
- It does not append to the agenda unless `--append` is passed.
- `--vault-path` is optional only when `OBSIDIAN_VAULT_PATH` is set in `.env`; otherwise `--vault-path` is required.
- If `resources/clarity-corrections.csv` exists (or `--corrections-csv` is passed), corrections are applied before automated rules.

Default invocation guidance for non-Obsidian users:
- Pass `--vault-path` explicitly.
- Pass `--output-json <path>` to capture machine-readable output in your own workflow/artifacts.

Feedback/training workflow:
- Review generated markdown/JSON output.
- Add accepted corrections to `clarity-corrections.csv` using columns:
  - `date` (optional), `source_event`, `project`, `task_name`, `task_code`, `hours` (optional)
- Re-run classification; exact `source_event` matches (and optional date match) override automated classification.

Planned enhancement (TODO):
- Add payroll-period rollup mode using `--start-date` and `--end-date` (15-day payroll calendar window) to generate a consolidated rollup artifact in addition to per-day JSON files.

## Portability Contract (Repository-Independent)
To use this skill in any repository, provide three pluggable components:
1. `activities_loader(input_source) -> list[dict]`
   - Returns normalized activities with fields: `title`, optional `notes`, optional `duration_hours`, optional `start`/`end`.

2. `clarity_defs_loader(csv_source) -> list[dict]`
   - Parses CSV into definitions with: `project`, `task_name`, `task_code`, optional `inactive`.

3. `classifier(activities, clarity_defs, date_str) -> summary_dict`
   - Applies the deterministic algorithm described below (rule-first, fallback, tie-breakers).

This skill defines the behavior and data contract, not a required file layout or CLI.

## Reference Invocation (Python)
```python
# Example only: wire these to your repo's implementation.
activities = activities_loader(input_source)
clarity_defs = clarity_defs_loader(csv_source)
summary = classifier(activities, clarity_defs, "2026-05-28")
print(summary)
```

## Algorithm

1) Normalize text (lowercase, NFKC, strip punctuation, collapse whitespace). Construct `match_text = title + ' ' + notes` (notes optional) before normalization. Tokenize on whitespace for downstream scoring.

2) For each rule in `CLASSIFICATION_RULES` (top to bottom): if `rule.match(match_text)` then
   a) find CSV rows matching `rule.targets` (see 'targets' matching rules below);
   b) if multiple CSV rows match apply CSV tie-breaker (exact `task_name` whole-word match > token overlap > smallest `task_code` lexicographically);
   c) select that CSV row and STOP (first-match-wins).

3) If no rule matched: perform fallback token-overlap scoring:
   - Tokenize `title+notes` by splitting on whitespace/punctuation, lowercase, remove English stopwords.
   - For each CSV candidate compute `score = (#shared_tokens)/(#tokens_in_candidate)`.
   - Select the highest score. Accept candidate only if `score >= 0.30`.
   - If top candidates tie, prefer longest common substring; if still tied pick the smallest `task_code` lexicographically.
   - If the top token-overlap score < 0.30 or there is a tie for top score, do not auto-assign: set event assignment to `{ 'project': 'Internal Meetings', 'task_code': 'INTERNAL', 'manual_review': true }` and include `candidate_scores` in output for human review.

4) If still no candidate: assign `project='Internal Meetings'`, `task_code='INTERNAL'`.

5) Invoke the LLM only when explicitly allowed: only if (a) no rule matched AND top token-overlap score < 0.25, or (b) there is a tie between top candidates. Provide the LLM the normalized text and top N CSV candidates. Require the LLM to return a `task_code` present in the CSV. If it returns an unknown code, mark the event `manual_review: true` and assign `INTERNAL`.

Notes on normalization and matching:
- Construct `match_text = title + ' ' + notes` (notes optional), then normalize by: lowercase, Unicode NFKC, remove punctuation, collapse whitespace. Tokenize on whitespace and apply keyword matching to normalized `match_text`.

CSV tie-breaker details:
- If a rule's targets match multiple CSV rows resolve deterministically: 1) prefer rows where `task_name` contains the target as an exact whole-word (case-insensitive); 2) then prefer highest token-overlap score; 3) then pick the row with the smallest `task_code` lexicographically; log the tie and chosen row in `resolution_log`.

Fallback scoring tie-breaker:
- If top candidates tie on score, prefer the candidate with the longest common substring with the normalized `match_text`; if still tied pick the smallest `task_code` lexicographically. If no candidate passes the score threshold treat as no candidate (see step 3 handling above).

## How To Extend (Team Learning Loop)
Maintain an ordered rule dictionary/list in your implementation. Keep it in one place so teams can update mappings quickly as patterns evolve.

Rule entry format (explicit match semantics):
```python
{
  'name': 'short_rule_id',
  'keywords': { 'mode': 'any', 'terms': ['bootcamp','training'], 'match_type': 'case-insensitive-whole-word' },
  'targets': [ { 'field':'task_name', 'fragment':'Training', 'match':'substring', 'case_sensitive': False } ]
}
```

Guidelines (deterministic):
- Rules are evaluated in order from top to bottom. Apply the first rule whose match condition is satisfied and stop evaluating lower-priority rules (first-match-wins).
- Prefer narrow, specific rules before broad ones.
- Align `targets` with exact CSV fields (`project`, `task_name`, `task_code`) and use the `targets` structure above to be explicit about which field to match and how.

Developer checklist (to be enforced by CI):
1) New rule added at intended index with unique `name`;
2) Provide 2 positive and 2 negative unit tests (input text and expected `task_code`);
3) Run CSV header validation;
4) Run linter that checks for subsuming rules (broad rule above narrow rule) and warns.

Unit-test template: add `classification/tests/test_rule_template.py` with simple test cases that exercise the rule behavior and the CSV validation.

If multiple CSV rows match a rule's target fragment resolve deterministically: 1) prefer rows where `task_name` contains the target as an exact whole-word (case-insensitive); 2) then prefer highest token-overlap; 3) then pick smallest `task_code` lexicographically. Include a `resolution_log` entry describing the chosen row.

## Suggested Repository Layout (Optional)
This is a recommendation only for teams maintaining shared skills:
- `skills/clarity-classification/SKILL.md` (this file)
- `skills/clarity-classification/examples/` (sample input and output)
- `skills/clarity-classification/tests/` (behavior tests against the contract)
- `skills/clarity-classification/changelog.md` (rule updates over time)

## Quality Checklist
- Daily activities include meaningful titles; notes improve accuracy.
- Clarity CSV is current for the reporting period and passes header validation.
- New rules are validated with tests before rollout.
- Ambiguous activities default to Internal Meetings unless explicitly mapped or flagged for manual review.

## Known Limits
- Deterministic keyword logic can misclassify vague titles.
- CSV naming quality strongly affects match accuracy.
- LLM classifier hook is optional and should remain secondary to deterministic logic; it is invoked only under the conditions documented in the Algorithm section.
