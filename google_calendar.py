
import os
import datetime
from dateutil import parser
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']
CREDENTIALS_PATH = "credentials.json"  
TOKEN_PATH = "token.json"

def get_creds():
    creds = None
    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)
            creds = flow.run_local_server(port=8080)
        with open(TOKEN_PATH, 'w') as f:
            f.write(creds.to_json())
    return creds

def get_events_for_date(date: datetime.date, max_results=50):
    """Return list of events for a particular date (local timezone)."""
    creds = get_creds()
    service = build('calendar', 'v3', credentials=creds)
    start = datetime.datetime.combine(date, datetime.time.min).isoformat() + 'Z'
    end = datetime.datetime.combine(date, datetime.time.max).isoformat() + 'Z'
    events_result = service.events().list(
        calendarId='primary', timeMin=start, timeMax=end,
        singleEvents=True, orderBy='startTime', maxResults=max_results).execute()
    events = events_result.get('items', [])
    # Normalize
    normalized = []
    for e in events:
        start = e.get('start', {}).get('dateTime') or e.get('start', {}).get('date')
        end = e.get('end', {}).get('dateTime') or e.get('end', {}).get('date')
        normalized.append({
            "summary": e.get("summary"),
            "start": start,
            "end": end,
            "location": e.get("location"),
            "description": e.get("description"),
        })
    return normalized
def get_events(query_or_date):
    """Accepts either a date (datetime.date) or a natural language phrase."""
    import re

    if isinstance(query_or_date, datetime.date):
        date = query_or_date
    else:
        text = str(query_or_date).lower().strip()

        # --- handle English & French keywords ---
        if any(word in text for word in ["today", "aujourd"]):
            date = datetime.date.today()
        elif any(word in text for word in ["tomorrow", "demain"]):
            date = datetime.date.today() + datetime.timedelta(days=1)
        else:
            # --- try to find a date like "25 october", "oct 25", "25/10", etc. ---
            try:
                text = re.sub(r"[^a-z0-9/\-: ]", "", text)  # clean up punctuation
                parsed = parser.parse(text, fuzzy=True)
                date = parsed.date()
            except Exception:
                return "❌ Sorry, I couldn't understand the date."

    # --- Fetch events from Google Calendar ---
    events = get_events_for_date(date)

    if not events:
        return f"No events found for {date}."
    
    response = f"📅 Events for {date}:\n"
    for e in events:
        response += f"- {e['summary']} ({e['start']} → {e['end']})\n"
    return response
