#!/usr/bin/env python3
"""
Obsidian Daily Sync Script (agenda.py)
Syncs Todoist tasks and Microsoft Graph Outlook calendar to Obsidian daily notes.

This script runs daily to pull:
1. Todoist tasks (overdue, due today, due this week)
2. Outlook calendar events via Microsoft Graph API (filtered for relevant meetings)
3. Combines them into a populated work note for Sonic Automotive
4. Writes to: Work/Sonic/Daily/YYYY-MM-DD_Agenda.md

Authentication: Uses Device Flow (user logs in via browser, no stored passwords)

USAGE:
    python sync_daily_notes.py              # Normal sync (first run: login via browser)
    python sync_daily_notes.py --test       # Test connectivity only
    python sync_daily_notes.py --verbose    # Detailed output
    python sync_daily_notes.py --help       # Show options
"""

import os
import re
import sys
import argparse
import json
from datetime import datetime, timedelta
from pathlib import Path
from dotenv import load_dotenv
from todoist_api_python.api import TodoistAPI
import httpx
import msal
import requests
import logging
from exchangelib import Credentials, Account, Configuration

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# ============================================================================
# CONFIGURATION - Update these to match your setup
# ============================================================================
STAKEHOLDER_NAMES = ["Gabe", "Stephen"]  # Who needs visibility
DELEGATION_TARGETS = ["Thayra", "Raj", "Jim"]  # Team members for delegation
COMPANY_NAME = "Sonic Automotive"  # Your company name
TODOIST_PROJECT_NAME = None  # If None, pulls from all projects

# Calendar event filters - events matching these are skipped
SKIP_PATTERNS = [
    "lunch",
    "focus time",
    "ooo",
    "out of office",
    "protected",
    "break",
]
MIN_EVENT_DURATION_MINUTES = 30
# ============================================================================

class GraphAPIClient:
    """Microsoft Graph API client with interactive browser-based authentication."""
    
    # Public client ID for Outlook/Graph access
    CLIENT_ID = "04b07795-8ddb-461a-bbee-02f9e1bf7b46"  # Azure CLI default
    GRAPH_ENDPOINT = "https://graph.microsoft.com/v1.0"
    AUTHORITY = "https://login.microsoftonline.com/common"
    SCOPES = ["Calendars.Read"]
    
    def __init__(self, client_id=None):
        """Initialize Graph API client with MSAL and interactive auth."""
        self.client_id = client_id or self.CLIENT_ID
        self.access_token = None
        self.token_cache_file = Path.home() / ".cache" / "obsidian_sync_token.json"
        self.token_cache_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize MSAL app
        self.app = msal.PublicClientApplication(
            client_id=self.client_id,
            authority=self.AUTHORITY
        )
        
        # Try to load cached token
        self._load_cached_token()
    
    def _load_cached_token(self):
        """Load cached access token if it exists and is still valid."""
        try:
            if self.token_cache_file.exists():
                with open(self.token_cache_file, 'r') as f:
                    cache = json.load(f)
                    self.access_token = cache.get('access_token')
                    expires_at = cache.get('expires_at')
                    
                    # Check if token is still valid (with 5 min buffer)
                    if expires_at and datetime.fromtimestamp(expires_at) > datetime.now() + timedelta(minutes=5):
                        logger.debug("Using cached access token")
                        return
                    
                    self.access_token = None
        except Exception as e:
            logger.debug(f"Could not load cached token: {e}")
            self.access_token = None
    
    def _save_cached_token(self, token):
        """Cache the access token with expiration time."""
        try:
            expires_at = (datetime.now() + timedelta(seconds=3600)).timestamp()
            cache = {
                'access_token': token,
                'expires_at': expires_at
            }
            
            with open(self.token_cache_file, 'w') as f:
                json.dump(cache, f)
            logger.debug("Cached access token")
        except Exception as e:
            logger.warning(f"Could not cache token: {e}")
    
    def ensure_authenticated(self):
        """Ensure we have a valid access token via interactive browser login."""
        if self.access_token:
            logger.debug("Using existing access token")
            return True
        
        print("\n" + "="*70)
        print("🔐 MICROSOFT OUTLOOK AUTHENTICATION")
        print("="*70 + "\n")
        print("A browser window will open for you to sign in...")
        print("Sign in with your Microsoft account that has Outlook calendar access.\n")
        
        try:
            # Try interactive authentication (opens browser)
            result = self.app.acquire_token_interactive(
                scopes=self.SCOPES,
                prompt='select_account'
            )
            
            if 'access_token' in result:
                self.access_token = result['access_token']
                self._save_cached_token(self.access_token)
                print("✅ Authentication successful!\n")
                logger.info(f"Authenticated with Microsoft Graph (expires in {result.get('expires_in', 3600)}s)")
                return True
            else:
                error = result.get('error_description', result.get('error', 'Unknown error'))
                logger.error(f"Authentication failed: {error}")
                print(f"❌ Authentication failed: {error}\n")
                return False
                
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            print(f"❌ Authentication error: {e}\n")
            return False
    
    def get_calendar_events(self, start_date=None, end_date=None):
        """Fetch calendar events from a date range."""
        if not self.ensure_authenticated():
            logger.error("Not authenticated - cannot fetch calendar events")
            return []
        
        if not start_date:
            start_date = datetime.now().date()
        if not end_date:
            end_date = start_date
        
        # Format dates for Graph API (RFC 3339)
        start_datetime = datetime.combine(start_date, datetime.min.time())
        end_datetime = datetime.combine(end_date, datetime.max.time())
        
        events_url = f"{self.GRAPH_ENDPOINT}/me/calendarview"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json',
            'Prefer': 'outlook.timezone="UTC"'
        }
        params = {
            'startDateTime': start_datetime.isoformat() + 'Z',
            'endDateTime': end_datetime.isoformat() + 'Z',
            '$orderby': 'start/dateTime',
            '$top': 50
        }
        
        try:
            logger.debug(f"Fetching calendar events from {start_date} to {end_date}")
            logger.debug(f"Request URL: {events_url}")
            logger.debug(f"Request params: {params}")
            
            response = requests.get(events_url, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            events = data.get('value', [])
            
            logger.info(f"Retrieved {len(events)} calendar events")
            
            # Convert to simple object format
            formatted_events = []
            for event in events:
                try:
                    formatted_event = {
                        'subject': event.get('subject', 'Untitled'),
                        'start': event.get('start', {}),
                        'end': event.get('end', {}),
                        'is_all_day': event.get('isAllDay', False),
                        'location': event.get('location', {}),
                        'body_preview': event.get('bodyPreview', '')
                    }
                    formatted_events.append(formatted_event)
                    logger.debug(f"  Event: {formatted_event['subject']} at {formatted_event['start'].get('dateTime', 'N/A')}")
                except Exception as e:
                    logger.error(f"Error processing event: {e}")
            
            return formatted_events
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching calendar events: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response status: {e.response.status_code}")
                logger.error(f"Response body: {e.response.text}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error fetching calendar: {e}")
            return []


class GraphAPIClient:
    """Client for accessing Microsoft Graph API with direct token authentication."""
    
    def __init__(self, access_token=None):
        self.access_token = access_token
        self.GRAPH_ENDPOINT = "https://graph.microsoft.com/v1.0"
    
    def get_calendar_events(self, start_date, end_date):
        """Fetch calendar events from Microsoft Graph API."""
        if not self.access_token:
            logger.error("No access token provided for Graph API")
            return []
        
        # Format dates for Graph API (RFC 3339)
        start_datetime = datetime.combine(start_date, datetime.min.time())
        end_datetime = datetime.combine(end_date, datetime.max.time())
        
        events_url = f"{self.GRAPH_ENDPOINT}/me/calendarview"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json',
            'Prefer': 'outlook.timezone="Eastern Standard Time"'
        }
        params = {
            'startDateTime': start_datetime.isoformat() + 'Z',
            'endDateTime': end_datetime.isoformat() + 'Z',
            '$orderby': 'start/dateTime',
            '$top': 50
        }
        
        try:
            logger.debug(f"Fetching calendar events from {start_date} to {end_date}")
            logger.debug(f"Request URL: {events_url}")
            logger.debug(f"Request params: {params}")
            
            response = requests.get(events_url, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            events = data.get('value', [])
            
            logger.info(f"Retrieved {len(events)} calendar events")
            
            # Convert to simple object format
            formatted_events = []
            for event in events:
                try:
                    formatted_event = {
                        'subject': event.get('subject', 'Untitled'),
                        'start': event.get('start', {}),
                        'end': event.get('end', {}),
                        'is_all_day': event.get('isAllDay', False),
                        'location': event.get('location', {}),
                        'body_preview': event.get('bodyPreview', '')
                    }
                    formatted_events.append(formatted_event)
                    logger.debug(f"  Event: {formatted_event['subject']} at {formatted_event['start'].get('dateTime', 'N/A')}")
                except Exception as e:
                    logger.error(f"Error processing event: {e}")
            
            return formatted_events
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching calendar events: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response status: {e.response.status_code}")
                logger.error(f"Response body: {e.response.text}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error fetching calendar: {e}")
            return []


class ExchangeClient:
    """Client for accessing Exchange/Outlook calendar via exchangelib."""
    
    def __init__(self, email, password, server='outlook.office365.com'):
        self.email = email
        self.password = password
        self.server = server
        self.account = None
        
        try:
            credentials = Credentials(username=email, password=password)
            config = Configuration(server=server, credentials=credentials)
            self.account = Account(primary_smtp_address=email, config=config, autodiscover=False)
            logger.info(f"Exchange account initialized for {email}")
        except Exception as e:
            logger.error(f"Failed to initialize Exchange account: {e}")
            raise
    
    def get_calendar_events(self, start_date, end_date):
        """Fetch calendar events from Exchange."""
        if not self.account:
            logger.error("Exchange account not initialized")
            return []
        
        try:
            # Get calendar folder
            calendar = self.account.calendar
            
            # Build filter for date range
            start_datetime = datetime.combine(start_date, datetime.min.time())
            end_datetime = datetime.combine(end_date, datetime.max.time())
            
            # Query events
            events = calendar.filter(
                start__range=(start_datetime, end_datetime)
            ).order_by('start')
            
            # Convert to dict format
            formatted_events = []
            for event in events:
                try:
                    formatted_event = {
                        'subject': event.subject or 'Untitled',
                        'start': {
                            'dateTime': event.start.isoformat() + 'Z',
                            'timeZone': 'UTC'
                        },
                        'end': {
                            'dateTime': event.end.isoformat() + 'Z',
                            'timeZone': 'UTC'
                        },
                        'is_all_day': event.is_all_day,
                        'location': {
                            'displayName': event.location or ''
                        },
                        'body_preview': getattr(event, 'text_body', '') or ''
                    }
                    formatted_events.append(formatted_event)
                except Exception as e:
                    logger.error(f"Error processing Exchange event: {e}")
            
            logger.info(f"Retrieved {len(formatted_events)} calendar events from Exchange")
            return formatted_events
            
        except Exception as e:
            logger.error(f"Error fetching calendar events from Exchange: {e}")
            return []


class ObsidianDailySync:
    def __init__(self):
        """Initialize the sync service."""
        self.todoist_token = os.getenv('TODOIST_API_TOKEN')
        self.vault_path = Path(os.getenv('OBSIDIAN_VAULT_PATH'))
        
        # Graph API access token
        self.graph_access_token = os.getenv('GRAPH_ACCESS_TOKEN')
        
        # Output path: Work/Sonic/Daily/YYYY-MM-DD_Agenda.md
        self.work_folder = "Work"
        self.company_folder = "Sonic"
        self.daily_notes_folder = "Daily"
        
        # Template path: Resources/Templates/sonic-daily-template.md
        self.template_path = self.vault_path / "Resources" / "Templates" / "sonic-daily-template.md"
        
        self.todoist = None
        self.graph_client = None
        
        self._initialize_clients()
    
    def _initialize_clients(self):
        """Initialize Todoist and Microsoft Graph clients."""
        try:
            # Initialize Todoist
            if self.todoist_token:
                todoist_client = httpx.Client(trust_env=False)
                self.todoist = TodoistAPI(self.todoist_token, client=todoist_client)
                logger.info("Todoist client initialized")
            else:
                logger.warning("TODOIST_API_TOKEN not set")
        except Exception as e:
            logger.error(f"Failed to initialize Todoist: {e}")
        
        try:
            # Initialize Microsoft Graph client
            if self.graph_access_token:
                self.graph_client = GraphAPIClient(access_token=self.graph_access_token)
                logger.info("Microsoft Graph client initialized")
            else:
                logger.warning("GRAPH_ACCESS_TOKEN not set")
        except Exception as e:
            logger.error(f"Failed to initialize Graph client: {e}")
    
    def get_todoist_tasks(self):
        """Fetch tasks from Todoist and organize by due date."""
        if not self.todoist:
            return {'overdue': [], 'due_today': [], 'due_this_week': []}
        
        try:
            today = datetime.now().date()
            week_end = today + timedelta(days=7)
            
            overdue = []
            due_today = []
            due_this_week = []
            
            # Get all active tasks
            tasks_paginator = self.todoist.get_tasks()
            paginator_list = list(tasks_paginator)
            tasks = paginator_list[0] if paginator_list else []
            
            for task in tasks:
                # Skip completed tasks (completed_at is not None)
                if task.completed_at is not None:
                    continue
                
                # Skip tasks without due dates
                if not task.due:
                    continue
                
                # Get due date (handle both string and date object)
                if isinstance(task.due.date, str):
                    due_date = datetime.fromisoformat(task.due.date).date()
                else:
                    # Handle datetime.datetime objects by extracting the date
                    due_date = task.due.date.date() if hasattr(task.due.date, 'date') else task.due.date
                
                # Categorize task
                if due_date < today:
                    overdue.append(task)
                elif due_date == today:
                    due_today.append(task)
                elif due_date <= week_end:
                    due_this_week.append(task)
            
            return {
                'overdue': overdue,
                'due_today': due_today,
                'due_this_week': due_this_week
            }
        except Exception as e:
            logger.error(f"Error fetching Todoist tasks: {e}")
            return {'overdue': [], 'due_today': [], 'due_this_week': []}

    def get_all_active_todoist_tasks(self):
        """Fetch all active Todoist tasks for matching against checked note items."""
        if not self.todoist:
            return []

        try:
            tasks_paginator = self.todoist.get_tasks()
            paginator_list = list(tasks_paginator)
            tasks = []
            for page in paginator_list:
                tasks.extend(page)
            return tasks
        except Exception as e:
            logger.error(f"Error fetching all active Todoist tasks: {e}")
            return []

    @staticmethod
    def normalize_task_text(text):
        """Normalize task text for matching by content."""
        if not text:
            return ""
        normalized = re.sub(r'\s+', ' ', text).strip().lower()
        return normalized

    @staticmethod
    def clean_checked_task_text(text):
        """Remove due date and priority suffixes from a checked task line."""
        cleaned = text.strip()
        cleaned = re.sub(r'\s*\(due:\s*\d{4}-\d{2}-\d{2}\)\s*$', '', cleaned)
        cleaned = re.sub(r'\s*[🔴🟠🟡]+\s*$', '', cleaned)
        return cleaned.strip()

    def extract_checked_todoist_task_texts(self, content):
        """Extract checked task texts from the task sections of the agenda note."""
        if not content:
            return []

        section_pattern = r'### (Overdue|Due today|Due this week)\s*(.*?)(?=\n### |\n---|\Z)'
        checked_texts = []

        for match in re.finditer(section_pattern, content, flags=re.S):
            section_body = match.group(2)
            for line in section_body.splitlines():
                item_match = re.match(r'^\s*[-*+]\s*\[[xX]\]\s*(.+)$', line)
                if item_match:
                    cleaned = self.clean_checked_task_text(item_match.group(1))
                    if cleaned:
                        checked_texts.append(cleaned)

        return checked_texts

    def complete_checked_todoist_items(self, note_content):
        """Mark checked Todoist task items in the agenda note as complete in Todoist."""
        if not self.todoist or not note_content:
            return 0

        checked_texts = self.extract_checked_todoist_task_texts(note_content)
        if not checked_texts:
            return 0

        active_tasks = self.get_all_active_todoist_tasks()
        if not active_tasks:
            return 0

        tasks_by_normalized = {}
        for task in active_tasks:
            task_text = self.normalize_task_text(task.content)
            tasks_by_normalized.setdefault(task_text, []).append(task)

        completed_count = 0
        for checked_text in checked_texts:
            normalized = self.normalize_task_text(checked_text)
            if normalized in tasks_by_normalized and tasks_by_normalized[normalized]:
                task = tasks_by_normalized[normalized].pop(0)
                try:
                    if self.todoist.complete_task(task.id):
                        completed_count += 1
                        logger.info(f"Marked Todoist task complete from note: {task.content} ({task.id})")
                    else:
                        logger.warning(f"Failed to mark Todoist task complete: {task.content} ({task.id})")
                except Exception as e:
                    logger.error(f"Error completing Todoist task '{task.content}' ({task.id}): {e}")

        return completed_count

    def format_tasks_markdown(self, tasks, category="today"):
        """Format tasks as markdown list with due dates."""
        if not tasks:
            return "*No tasks*"
        
        formatted = []
        for task in tasks:
            # Include due date for overdue and this_week categories
            due_date_str = ""
            if category in ["overdue", "this_week"] and task.due:
                due_date_str = f" (due: {task.due.date})"
            
            # Priority indicator
            priority_indicator = ""
            if task.priority > 1:
                priority_map = {4: "🔴", 3: "🟠", 2: "🟡"}
                priority_indicator = f" {priority_map.get(task.priority, '')}"
            
            formatted.append(f"- [ ] {task.content}{due_date_str}{priority_indicator}")
        
        return "\n".join(formatted)
    
    def get_exchange_calendar_events(self):
        """Fetch today's calendar events from Microsoft Graph."""
        if not self.graph_client:
            return []
        
        try:
            today = datetime.now().date()
            events = self.graph_client.get_calendar_events(today, today)
            return events
        except Exception as e:
            logger.error(f"Error fetching calendar events: {e}")
            return []
    
    def should_include_event(self, event):
        """
        Return True if this event should appear in the note.
        
        Skips:
        - All-day events
        - Events matching skip patterns (lunch, focus time, etc.)
        - Events under MIN_EVENT_DURATION_MINUTES
        """
        # Skip all-day events
        if event.get('is_all_day', False):
            return False
        
        # Skip by title pattern
        title_lower = event.get('subject', '').lower()
        for pattern in SKIP_PATTERNS:
            if pattern in title_lower:
                return False
        
        # Skip short events
        try:
            start_str = event.get('start', {}).get('dateTime')
            end_str = event.get('end', {}).get('dateTime')
            
            if start_str and end_str:
                start = datetime.fromisoformat(start_str.replace('Z', '+00:00'))
                end = datetime.fromisoformat(end_str.replace('Z', '+00:00'))
                duration_minutes = (end - start).total_seconds() / 60
                if duration_minutes < MIN_EVENT_DURATION_MINUTES:
                    return False
        except Exception as e:
            logger.debug(f"Could not calculate event duration: {e}")
        
        return True
    
    def extract_event_location(self, event):
        """Extract location or meeting link from event."""
        location_parts = []
        
        # Add physical location if present
        location_obj = event.get('location', {})
        if location_obj and location_obj.get('displayName'):
            location_parts.append(location_obj.get('displayName'))
        
        # Try to extract Teams/Zoom link from body preview
        body_preview = event.get('body_preview', '')
        if body_preview:
            # Look for Teams link
            teams_pattern = r'https://teams\.microsoft\.com[^\s\)]*'
            zoom_pattern = r'https://zoom\.us[^\s\)]*'
            
            teams_match = re.search(teams_pattern, body_preview)
            zoom_match = re.search(zoom_pattern, body_preview)
            
            if teams_match:
                location_parts.append("Teams")
            elif zoom_match:
                location_parts.append("Zoom")
        
        return " | ".join(location_parts) if location_parts else ""
    
    def format_calendar_table(self, events):
        """Format calendar events as markdown table with Location/Link column."""
        # Filter events based on criteria
        filtered_events = [e for e in events if self.should_include_event(e)]
        
        if not filtered_events:
            return "*No calendar events*"
        
        # Sort events by start time
        def get_start_time(event):
            try:
                start_str = event.get('start', {}).get('dateTime')
                if start_str:
                    return datetime.fromisoformat(start_str.replace('Z', '+00:00'))
            except:
                pass
            return datetime.now()
        
        sorted_events = sorted(filtered_events, key=get_start_time)
        
        table = "| Time | Event | Location/Link |\n|---|---|---|\n"
        
        for event in sorted_events:
            try:
                start_obj = event.get('start', {})
                start_str = start_obj.get('dateTime')
                timezone = start_obj.get('timeZone', 'UTC')
                
                if start_str:
                    start_dt = datetime.fromisoformat(start_str.replace('Z', '+00:00'))
                    
                    # Only convert if the timezone is UTC (not already in Eastern Time)
                    if timezone == 'UTC':
                        start_dt = start_dt.replace(hour=start_dt.hour - 4)
                    
                    start_time = start_dt.strftime("%I:%M %p")
                else:
                    start_time = "--:-- --"
            except:
                start_time = "--:-- --"
            
            subject = event.get('subject', 'No title')
            # Truncate long titles
            if len(subject) > 40:
                subject = subject[:37] + "..."
            
            location = self.extract_event_location(event)
            
            logger.debug(f"Event '{subject}': {start_str} ({timezone}) -> {start_time}")
            table += f"| {start_time} | {subject} | {location} |\n"
            logger.debug(f"Added to table: | {start_time} | {subject} | {location} |")
        
        return table
    
    def get_daily_note_path(self, date=None):
        """Get the path to today's agenda note."""
        if date is None:
            date = datetime.now()
        
        # Path: Work/Sonic/Daily/YYYY-MM-DD_Agenda.md
        filename = date.strftime("%Y-%m-%d_Agenda.md")
        return self.vault_path / self.work_folder / self.company_folder / self.daily_notes_folder / filename
    
    def read_daily_note(self, path):
        """Read the daily note file."""
        if not path.exists():
            logger.warning(f"Daily note not found: {path}")
            return None
        
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            logger.error(f"Error reading daily note: {e}")
            return None
    
    def load_template(self):
        """Load the sonic-daily-template to use as a base for new daily notes."""
        if not self.template_path.exists():
            logger.error(f"Template not found: {self.template_path}")
            return None
        
        try:
            with open(self.template_path, 'r', encoding='utf-8') as f:
                template_content = f.read()
            logger.info(f"Loaded template from: {self.template_path}")
            return template_content
        except Exception as e:
            logger.error(f"Error loading template: {e}")
            return None
    
    def write_daily_note(self, path, content):
        """Write content to the daily note file."""
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)
            logger.info(f"Daily note updated: {path}")
            return True
        except Exception as e:
            logger.error(f"Error writing daily note: {e}")
            return False
    
    def update_daily_note_content(self, content, tasks, events):
        """Update template placeholders with fetched data."""
        # Format task sections
        overdue_tasks = self.format_tasks_markdown(tasks['overdue'], category='overdue')
        due_today_tasks = self.format_tasks_markdown(tasks['due_today'], category='today')
        due_this_week_tasks = self.format_tasks_markdown(tasks['due_this_week'], category='this_week')
        
        # Format calendar table
        calendar_table = self.format_calendar_table(events)
        
        # Generate meeting notes stubs for included events
        filtered_events = [e for e in events if self.should_include_event(e)]
        
        # Sort by start time
        def get_start_time(event):
            try:
                start_str = event.get('start', {}).get('dateTime')
                if start_str:
                    return datetime.fromisoformat(start_str.replace('Z', '+00:00'))
            except:
                pass
            return datetime.now()
        
        sorted_events = sorted(filtered_events, key=get_start_time)
        
        meeting_notes = ""
        for event in sorted_events:
            try:
                start_str = event.get('start', {}).get('dateTime')
                if start_str:
                    start_dt = datetime.fromisoformat(start_str.replace('Z', '+00:00'))
                    time_str = start_dt.strftime("%I:%M %p")
                else:
                    time_str = "--:-- --"
            except:
                time_str = "--:-- --"
            
            subject = event.get('subject', 'Untitled')
            meeting_notes += f"### {time_str} — {subject}\n\n"
        
        # Replace placeholders
        updated_content = content.replace('{{overdue_tasks}}', overdue_tasks)
        updated_content = updated_content.replace('{{due_today_tasks}}', due_today_tasks)
        updated_content = updated_content.replace('{{due_this_week_tasks}}', due_this_week_tasks)
        updated_content = updated_content.replace('{{calendar_table}}', calendar_table)
        updated_content = updated_content.replace('{{meeting_notes}}', meeting_notes.strip())
        
        return updated_content
    
    def test_connectivity(self):
        """Test connectivity to Todoist, Microsoft Graph, and Obsidian."""
        print("\n" + "="*70)
        print("🧪 CONNECTIVITY TEST")
        print("="*70 + "\n")
        
        results = {
            'todoist': False,
            'graph': False,
            'vault': False,
            'daily_note': False
        }
        
        # Test Todoist
        print("Testing Todoist API...")
        try:
            if not self.todoist_token:
                print("  ❌ TODOIST_API_TOKEN not set in .env")
            else:
                tasks_paginator = self.todoist.get_tasks()
                paginator_list = list(tasks_paginator)
                tasks = paginator_list[0] if paginator_list else []
                task_count = len(tasks)
                print(f"  ✅ Todoist connected! Found {task_count} tasks")
                results['todoist'] = True
        except Exception as e:
            print(f"  ❌ Todoist error: {e}")
        
        # Test Microsoft Graph API
        print("\nTesting Microsoft Graph API...")
        try:
            if not self.graph_access_token:
                print("  ❌ GRAPH_ACCESS_TOKEN not set in .env")
            else:
                # Try to access calendar
                today = datetime.now().date()
                events = self.graph_client.get_calendar_events(today, today)
                print(f"  ✅ Graph API connected! Found {len(events)} events today")
                results['graph'] = True
        except Exception as e:
            print(f"  ❌ Graph API error: {e}")
        
        # Test Vault
        print("\nTesting Obsidian vault...")
        try:
            if not self.vault_path.exists():
                print(f"  ❌ Vault path not found: {self.vault_path}")
            else:
                print(f"  ✅ Vault path exists: {self.vault_path}")
                results['vault'] = True
        except Exception as e:
            print(f"  ❌ Vault error: {e}")
        
        # Test Template
        print("\nTesting sonic-daily-template...")
        try:
            if not self.template_path.exists():
                print(f"  ❌ Template not found: {self.template_path}")
                results['daily_note'] = False
            else:
                print(f"  ✅ Template found: {self.template_path}")
                results['daily_note'] = True
        except Exception as e:
            print(f"  ❌ Template error: {e}")
            results['daily_note'] = False
        
        # Summary
        print("\n" + "="*70)
        print("📊 TEST SUMMARY")
        print("="*70)
        
        passed = sum(1 for v in results.values() if v is True)
        failed = sum(1 for v in results.values() if v is False)
        warnings = sum(1 for v in results.values() if v is None)
        
        print(f"\n✅ Passed:   {passed}")
        print(f"❌ Failed:   {failed}")
        print(f"⚠️  Warnings: {warnings}")
        
        if failed == 0:
            print("\n✅ All systems ready! You can now run manual syncs.")
            return True
        else:
            print("\n❌ Fix the errors above before running sync.")
            print("\n💡 Troubleshooting tips:")
            if not self.todoist_token:
                print("  • Set TODOIST_API_TOKEN in .env")
                print("    (Get from: https://todoist.com/app/settings/integrations/developer)")
            if not results['graph']:
                print("  • Graph API auth failed - check GRAPH_ACCESS_TOKEN in .env")
                print("  • Make sure your access token is valid and has calendar permissions")
            if not results['daily_note']:
                print("  • Template not found - ensure sonic-daily-template.md exists at:")
                print(f"    {self.template_path}")
            return False
    
    def test_todoist_raw_tasks(self):
        """Test: Print all raw tasks returned from Todoist (for debugging)."""
        print("\n" + "="*70)
        print("🧪 TODOIST RAW TASKS TEST")
        print("="*70 + "\n")
        if not self.todoist:
            print("  ❌ Todoist client not initialized.")
            return
        try:
            tasks_paginator = self.todoist.get_tasks()
            paginator_list = list(tasks_paginator)
            tasks = paginator_list[0] if paginator_list else []
            print(f"Found {len(tasks)} tasks (raw):\n")
            for task in tasks:
                print(json.dumps(task.to_dict() if hasattr(task, 'to_dict') else task.__dict__, indent=2, default=str))
            print("\nDone.")
        except Exception as e:
            print(f"  ❌ Error fetching raw Todoist tasks: {e}")
    
    def sync(self):
        """Main sync function."""
        logger.info("Starting daily note sync...")
        
        try:
            # Get daily note path
            note_path = self.get_daily_note_path()
            
            # Read current content, or load template if note doesn't exist
            content = self.read_daily_note(note_path)
            completed_note_tasks = 0
            if content is None:
                logger.info("Daily note doesn't exist, creating from template...")
                content = self.load_template()
                if content is None:
                    logger.error("Cannot proceed without template")
                    return False
            else:
                completed_note_tasks = self.complete_checked_todoist_items(content)
                if completed_note_tasks > 0:
                    logger.info(f"Marked {completed_note_tasks} task(s) complete in Todoist from checked note items")

            # Fetch data
            logger.info("Fetching Todoist tasks...")
            tasks = self.get_todoist_tasks()
            
            # Fetch calendar - non-fatal if unavailable
            events = []
            calendar_available = True
            logger.info("Fetching Outlook calendar events via Microsoft Graph...")
            try:
                events = self.get_exchange_calendar_events()
            except Exception as e:
                calendar_available = False
                logger.warning(f"Calendar unavailable (will skip calendar events): {e}")
            
            # Update content
            updated_content = self.update_daily_note_content(content, tasks, events)
            
            # Write back
            success = self.write_daily_note(note_path, updated_content)
            
            if success:
                logger.info("Sync completed successfully")
                # Print summary
                print(f"\n✅ Daily note synced successfully!")
                print(f"📝 File: {note_path}")
                print(f"📋 Overdue tasks: {len(tasks['overdue'])}")
                print(f"✓ Due today: {len(tasks['due_today'])}")
                if not calendar_available:
                    print(f"📅 Calendar events: ⚠️ (unavailable - token expired or offline)")
                else:
                    print(f"📅 Calendar events: {len(events)}")
                if completed_note_tasks > 0:
                    print(f"✅ Marked {completed_note_tasks} checked task(s) complete in Todoist")
            
            return success
        
        except Exception as e:
            logger.error(f"Sync failed: {e}", exc_info=True)
            return False


def main():
    """Main entry point with CLI argument handling."""
    parser = argparse.ArgumentParser(
        description='Obsidian Daily Sync - Sync Todoist and Microsoft Graph Outlook Calendar to Obsidian',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python sync_daily_notes.py              # Run normal sync
  python sync_daily_notes.py --test       # Test connectivity only
  python sync_daily_notes.py --verbose    # Detailed output
  python sync_daily_notes.py --help       # Show this help

Schedule:
  • Windows Task Scheduler: M-F at 8:00 AM (via setup-task-scheduler.ps1)
  • Manual: Double-click run-sync.bat or run above commands
        """
    )
    
    parser.add_argument(
        '--test',
        action='store_true',
        help='Test connectivity to Todoist and Microsoft Graph API only (no sync)'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable detailed logging output'
    )
    parser.add_argument(
        '--no-backup',
        action='store_true',
        help='Skip creating backup of daily note before updating'
    )
    parser.add_argument(
        '--test-tasks',
        action='store_true',
        help='Print all raw Todoist tasks (debugging)'
    )
    
    args = parser.parse_args()
    
    # Configure logging verbosity
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Verbose mode enabled")
    
    try:
        sync = ObsidianDailySync()
        # Test Todoist raw tasks
        if args.test_tasks:
            sync.test_todoist_raw_tasks()
            exit(0)
        # Test mode
        if args.test:
            success = sync.test_connectivity()
            exit(0 if success else 1)
        # Normal sync mode
        logger.info("Starting daily note sync...")
        success = sync.sync()
        exit(0 if success else 1)
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        exit(1)


if __name__ == "__main__":
    main()
