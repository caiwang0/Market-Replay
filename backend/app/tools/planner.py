import aiohttp
import logging
from typing import List
from pydantic import BaseModel, Field
from langchain_core.tools import tool
import re
from dateparser import parse
from zoneinfo import ZoneInfo
import app.config as config

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)
TZ_MAP = {
    "jkt": "Asia/Jakarta",
    "sgt": "Asia/Singapore",
    "utc": "UTC",
}

class EventRequest(BaseModel):
    emails: List[str] = Field(..., description="List of attendee emails")
    summary: str = Field(..., description="Event title")
    description: str = Field(..., description="Event description")
    start: str = Field(..., description="Start time in natural language")
    end: str = Field(..., description="End time in natural language")
    timezone: str = Field("Asia/Jakarta", description="IANA timezone")

def parse_time_to_timestamp(time_str: str, default_tz: str = "Asia/Jakarta") -> str:
    """
    1. Scan for 'jkt', 'sgt', or 'utc' in the user string.
    2. If found, strip it out and use the matching IANA zone.
    3. Otherwise use default_tz for all-naïve times.
    4. Parse the stripped string as a naïve datetime.
    5. Attach the chosen timezone to get an aware datetime.
    6. Return its UNIX timestamp (always in UTC).
    """
    text = time_str.strip()
    lower = text.lower()

    # 1) Detect an explicit override
    detected_iana = None
    for abbr, iana in TZ_MAP.items():
        if re.search(fr"\b{abbr}\b", lower):
            detected_iana = iana
            # 2) remove the abbreviation so dateparser won't choke
            text = re.sub(fr"\b{abbr}\b", "", text, flags=re.IGNORECASE).strip()
            break

    tz_to_use = detected_iana or default_tz

    # 4) Parse naïvely (ignore any tz info)
    dt_naive = parse(
        text,
        settings={
            "RETURN_AS_TIMEZONE_AWARE": False,
            "PREFER_DATES_FROM": "future",
        },
    )
    if not dt_naive:
        raise ValueError(f"Cannot parse time: {time_str!r}")

    # 5) Localize to the chosen zone
    dt_aware = dt_naive.replace(tzinfo=ZoneInfo(tz_to_use))

    # 6) Return UTC-based timestamp
    return str(int(dt_aware.timestamp()))


async def get_tenant_access_token() -> str:
    """Get tenant access token using app credentials"""
    url = "https://open.larksuite.com/open-apis/auth/v3/tenant_access_token/internal"
    payload = {
        "app_id": config.LARK_APP_ID,
        "app_secret": config.LARK_APP_SECRET,
    }

    async with aiohttp.ClientSession() as sess:
        async with sess.post(url, json=payload) as resp:
            resp.raise_for_status()
            data = await resp.json()
            return data["tenant_access_token"]


async def get_open_ids_by_email(tenant_token: str, emails: List[str]) -> List[str]:
    """Get open IDs for email addresses"""
    url = "https://open.larksuite.com/open-apis/contact/v3/users/batch_get_id"
    headers = {"Authorization": f"Bearer {tenant_token}"}
    payload = {"emails": emails}

    async with aiohttp.ClientSession() as sess:
        async with sess.post(url, headers=headers, json=payload) as resp:
            resp.raise_for_status()
            data = await resp.json()
            return [user["user_id"] for user in data["data"]["user_list"]]

async def get_bot_calendar_id(tenant_token: str) -> tuple[str, str]:
    """Get the primary calendar ID and bot's open ID"""
    url = "https://open.larksuite.com/open-apis/calendar/v4/calendars/primary"
    headers = {
        "Authorization": f"Bearer {tenant_token}",
        "Content-Type": "application/json"
    }

    async with aiohttp.ClientSession() as sess:
        async with sess.post(url, headers=headers) as resp:
            resp.raise_for_status()
            data = await resp.json()

            try:
                if not data.get("data") or not data["data"].get("calendars"):
                    raise ValueError("No calendars found in response")

                calendar_data = data["data"]["calendars"][0]
                return (
                    calendar_data["calendar"]["calendar_id"],
                    calendar_data["user_id"]
                )
            except (KeyError, IndexError) as e:
                raise ValueError(f"Unexpected API response structure: {e}") from e

async def create_calendar_event(
    tenant_token: str,
    calendar_id: str,
    summary: str,
    description: str,
    start_timestamp: str,
    end_timestamp: str,
    owner_id: str,
    assign_hosts: list[str],
    join_meeting_permission: str = "only_organization_employees",
    need_notification: bool = True,
) -> str:
    """Create a calendar event and return event ID"""
    url = f"https://open.larksuite.com/open-apis/calendar/v4/calendars/{calendar_id}/events"
    headers = {
        "Authorization": f"Bearer {tenant_token}",
        "Content-Type": "application/json",
    }

    payload = {
        "summary": summary,
        "description": description,
        "need_notification": need_notification,
        "start_time": {"timestamp": start_timestamp},
        "end_time": {"timestamp": end_timestamp},
        "vchat": {
            "meeting_settings": {
                "owner_id": owner_id,
                "join_meeting_permission": join_meeting_permission,
                "assign_hosts": assign_hosts,
                "auto_record": False,
                "open_lobby": True,
                "allow_attendees_start": True
            }
        },
        "visibility": "default",
        "attendee_ability": "can_modify_event",
        "free_busy_status": "busy",
        "reminders": [{"minutes": 5}],
    }

    async with aiohttp.ClientSession() as sess:
        async with sess.post(url, headers=headers, json=payload) as resp:
            resp.raise_for_status()
            data = await resp.json()
            return data["data"]["event"]["event_id"]


async def add_attendees_to_event(
    tenant_token: str,
    calendar_id: str,
    event_id: str,
    attendee_open_ids: List[str],
) -> bool:
    """Add attendees to an existing calendar event"""
    url = f"https://open.larksuite.com/open-apis/calendar/v4/calendars/{calendar_id}/events/{event_id}/attendees"
    headers = {
        "Authorization": f"Bearer {tenant_token}",
        "Content-Type": "application/json",
    }

    payload = {
        "attendees": [
            {
                "type": "user",
                "is_optional": True,
                "user_id": open_id
            } for open_id in attendee_open_ids
        ],
        "need_notification": True
    }

    async with aiohttp.ClientSession() as sess:
        async with sess.post(url, headers=headers, json=payload) as resp:
            resp.raise_for_status()
            return True

@tool
async def schedule_meeting(
    emails: list[str],
    summary: str,
    description: str,
    start: str,
    end: str,
    timezone: str = "Asia/Jakarta",
) -> str:
    """
    Schedules a meeting in Lark calendar. ALWAYS use this tool when user asks to schedule a meeting, set up an appointment, or create a calendar event.

    Required input format:
    {
        "emails": ["email1@example.com", "email2@example.com"],
        "summary": "Meeting title",
        "description": "Meeting details",
        "start": "natural language time (e.g., 'tomorrow at 2pm')",
        "end": "natural language time (e.g., 'tomorrow at 3pm')",
        "timezone": "IANA timezone (e.g., 'Asia/Jakarta')"
    }
    """
    try:
        # Parse request into our model
        request = {
            "emails":emails,
            "summary":summary,
            "description":description,
            "start":start,
            "end":end,
            "timezone":timezone
        }
        req = EventRequest.model_validate(request)
        logger.info(f"Received meeting request: {req}")

        # Step 1: Get tenant access token
        logger.info("Getting tenant access token")
        tenant_token = await get_tenant_access_token()

        # Step 2: Get open_ids for attendee emails
        logger.info("Getting open_ids for attendees")
        attendee_open_ids = await get_open_ids_by_email(tenant_token, req.emails)

        # Step 3: Get bot's calendar ID AND userID
        logger.info("Getting bot's calendar ID")
        calendar_id, bot_user_id = await get_bot_calendar_id(tenant_token)

        # Step 4: Parse times to timestamps
        logger.info("Converting times to timestamps")
        start_timestamp = parse_time_to_timestamp(req.start, req.timezone)
        end_timestamp = parse_time_to_timestamp(req.end, req.timezone)

        # Step 5: Create calendar event
        logger.info("Creating calendar event")
            # Step 5: Create calendar event
        logger.info("Creating calendar event")
        event_id = await create_calendar_event(
            tenant_token=tenant_token,
            calendar_id=calendar_id,
            summary=req.summary,
            description=req.description,
            start_timestamp=start_timestamp,
            end_timestamp=end_timestamp,
            owner_id=bot_user_id,
            assign_hosts=attendee_open_ids + [bot_user_id],
        )


        # Step 6: Add attendees to event
        logger.info("Adding attendees to event")
        await add_attendees_to_event(
            tenant_token,
            calendar_id,
            event_id,
            attendee_open_ids,
        )

        logger.info(f"Meeting scheduled successfully. Event ID: {event_id}")
        return f"✅ Meeting scheduled successfully! Event ID: {event_id}"

    except Exception as e:
        logger.error(f"Error scheduling meeting: {str(e)}")
        return f"❌ Error scheduling meeting: {str(e)}"