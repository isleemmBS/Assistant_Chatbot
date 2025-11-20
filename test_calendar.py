import datetime
from google_calendar import get_events_for_date 

today = datetime.date.today()
events = get_events_for_date(today)

print(f"Events for {today}:")
for e in events:
    print(f"- {e['summary']} ({e['start']} → {e['end']})")
