"""
Service - Calendar Integration (Optional)
============================================
Google Calendar integration for scheduling deadlines extracted from contracts.
Gracefully degrades when credentials are not configured.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from backend.config import settings

logger = logging.getLogger(__name__)


def _get_calendar_service():
    """Build a Google Calendar API service object."""
    if not settings.GOOGLE_CALENDAR_CREDENTIALS_FILE:
        logger.info("Google Calendar credentials not configured — skipping")
        return None
    try:
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build

        creds = Credentials.from_authorized_user_file(
            settings.GOOGLE_CALENDAR_CREDENTIALS_FILE,
            scopes=["https://www.googleapis.com/auth/calendar"],
        )
        return build("calendar", "v3", credentials=creds)
    except Exception as exc:
        logger.warning("Could not initialise Google Calendar service: %s", exc)
        return None


def extract_and_schedule_dates(entities: Dict[str, Any]) -> Dict[str, Any]:
    """Extract dates from NER results and optionally schedule them."""
    dates = entities.get("dates", [])
    results: Dict[str, Any] = {"dates_found": len(dates), "scheduled": []}

    service = _get_calendar_service()
    if service is None:
        results["status"] = "calendar_not_configured"
        return results

    for date_str in dates:
        try:
            event_result = add_to_calendar({
                "summary": f"Contract Deadline: {date_str}",
                "description": "Auto-extracted deadline from legal document.",
                "date": date_str,
            })
            results["scheduled"].append(event_result)
        except Exception as exc:
            logger.warning("Failed to schedule %s: %s", date_str, exc)

    results["status"] = "ok"
    return results


def add_to_calendar(event_details: Dict[str, str]) -> str:
    """Add a single event to Google Calendar."""
    service = _get_calendar_service()
    if service is None:
        return "Calendar service unavailable"

    event = {
        "summary": event_details.get("summary", "Contract Deadline"),
        "description": event_details.get("description", ""),
        "start": {"date": event_details.get("date", ""), "timeZone": "UTC"},
        "end": {"date": event_details.get("date", ""), "timeZone": "UTC"},
    }
    try:
        created = service.events().insert(calendarId="primary", body=event).execute()
        return created.get("htmlLink", "created")
    except Exception as exc:
        logger.error("Calendar event creation failed: %s", exc)
        return f"Error: {exc}"


def get_calendar_events(start_date: str, end_date: str) -> List[Dict]:
    """Retrieve calendar events within a date range."""
    service = _get_calendar_service()
    if service is None:
        return []
    try:
        events_result = service.events().list(
            calendarId="primary",
            timeMin=start_date,
            timeMax=end_date,
            singleEvents=True,
            orderBy="startTime",
        ).execute()
        return events_result.get("items", [])
    except Exception as exc:
        logger.error("Failed to fetch calendar events: %s", exc)
        return []
