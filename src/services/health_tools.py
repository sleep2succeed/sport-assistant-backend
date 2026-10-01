"""LangChain tools for the Google Health API."""

from datetime import date, datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo

from google_health_api.api import GoogleHealthApi
from google_health_api.model.pagination import ListDataPointResult

from src.settings import settings

from langchain_core.tools import tool


LOCAL_TZ = ZoneInfo(settings.google_health.TIMEZONE)


def _serialize(obj: Any) -> Any:
    if hasattr(obj, "to_dict"):
        return obj.to_dict()
    return str(obj)


async def _collect_points(result: ListDataPointResult) -> list[dict[str, Any]]:
    points: list[dict[str, Any]] = []
    async for page in result:
        points.extend(
            {"name": p.name, "data": _serialize(p.data)} for p in page.data_points
        )
    return points


def _ensure_aware(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=LOCAL_TZ)
    return dt


def _parse_time(value: str | None, default: datetime) -> datetime:
    if value is None:
        return default
    dt = datetime.fromisoformat(value)
    return _ensure_aware(dt)


async def _collect_points_in_range(
    result: ListDataPointResult, start: datetime, end: datetime
) -> list[dict[str, Any]]:
    """Like _collect_points, but filters client-side by the point's own interval.

    Some data types (sleep, exercise) reject the server-side time filter the
    underlying library builds (HealthApiException: INVALID_DATA_POINT_FILTER_DATA_TYPE_MEMBER),
    so fetch unfiltered and filter locally by each point's start_time/end_time.
    """
    points: list[dict[str, Any]] = []
    async for page in result:
        for p in page.data_points:
            point_start = _ensure_aware(datetime.fromisoformat(p.data.start_time))
            if start <= point_start < end:
                points.append({"name": p.name, "data": _serialize(p.data)})
    return points


async def get_steps(
    api: GoogleHealthApi, start_time: str | None = None, end_time: str | None = None
) -> dict[str, Any]:
    """Step counts within a time range (defaults to the last 24 hours)."""
    end = _parse_time(end_time, datetime.now(LOCAL_TZ))
    start = _parse_time(start_time, end - timedelta(days=1))
    result = await api.steps.list(start_time=start, end_time=end)
    return {"data_points": await _collect_points(result)}


async def get_heart_rate(
    api: GoogleHealthApi, start_time: str | None = None, end_time: str | None = None
) -> dict[str, Any]:
    """Hourly-aggregated heart rate (min/max/avg bpm) within a time range.

    Raw heart-rate samples are far too dense to hand to an LLM (tens of thousands
    per day), so this aggregates to hourly buckets instead of returning every point.
    """
    end = _parse_time(end_time, datetime.now(LOCAL_TZ))
    start = _parse_time(start_time, end - timedelta(days=1))
    result = await api.heart_rate.list(start_time=start, end_time=end, page_size=1000)

    buckets: dict[datetime, list[int]] = {}
    async for page in result:
        for p in page.data_points:
            sample_time = p.data.sample_time.physical_time
            hour = datetime.fromisoformat(sample_time.replace("Z", "+00:00")).replace(
                minute=0, second=0, microsecond=0
            )
            buckets.setdefault(hour, []).append(p.data.beats_per_minute)

    hourly = [
        {
            "hour": hour.isoformat(),
            "avg_bpm": round(sum(bpms) / len(bpms), 1),
            "min_bpm": min(bpms),
            "max_bpm": max(bpms),
            "sample_count": len(bpms),
        }
        for hour, bpms in sorted(buckets.items())
    ]
    return {"hourly": hourly}


async def get_sleep(
    api: GoogleHealthApi, start_time: str | None = None, end_time: str | None = None
) -> dict[str, Any]:
    """Sleep sessions within a time range (defaults to the last 36 hours, covering last night)."""
    end = _parse_time(end_time, datetime.now(LOCAL_TZ))
    start = _parse_time(start_time, end - timedelta(hours=36))
    result = await api.sleep.list()
    return {"data_points": await _collect_points_in_range(result, start, end)}


async def get_activity(
    api: GoogleHealthApi, start_time: str | None = None, end_time: str | None = None
) -> dict[str, Any]:
    """Exercise/activity sessions within a time range (defaults to the last 7 days)."""
    end = _parse_time(end_time, datetime.now(LOCAL_TZ))
    start = _parse_time(start_time, end - timedelta(days=7))
    result = await api.exercise.list()
    return {"data_points": await _collect_points_in_range(result, start, end)}


async def get_resting_hr_and_hrv(
    api: GoogleHealthApi, start_date: str | None = None, end_date: str | None = None
) -> dict[str, Any]:
    """Daily resting heart rate and heart rate variability (defaults to the last 7 days)."""
    end_d = date.fromisoformat(end_date) if end_date else datetime.now(LOCAL_TZ).date()
    start_d = date.fromisoformat(start_date) if start_date else end_d - timedelta(days=7)
    start_dt = datetime.combine(start_d, datetime.min.time(), tzinfo=LOCAL_TZ)
    end_dt = datetime.combine(end_d, datetime.min.time(), tzinfo=LOCAL_TZ)

    resting_hr_result = await api.daily_resting_heart_rate.list(start_time=start_dt, end_time=end_dt)
    resting_hr = await _collect_points(resting_hr_result)

    hrv_result = await api.heart_rate_variability.list(start_time=start_dt, end_time=end_dt)
    hrv = await _collect_points(hrv_result)

    return {"resting_heart_rate": resting_hr, "heart_rate_variability": hrv}



def build_health_tools(api: GoogleHealthApi) -> list:
    @tool
    async def get_current_time_tool() -> dict:
        """Current local date and time in the user's timezone.

        Call this first whenever the user refers to a relative period
        ('yesterday', 'last night', 'this week', 'last 7 days', etc.) to
        compute accurate start_time/end_time arguments for the other tools.
        Returns an ISO-8601 timestamp with the UTC offset and the timezone key.
        """
        now = datetime.now(LOCAL_TZ)
        return {"now": now.isoformat(), "timezone": str(LOCAL_TZ)}

    @tool
    async def get_steps_tool(start_time: str | None = None, end_time: str | None = None) -> dict:
        """Step counts within a time range (defaults to the last 24 hours)."""
        return await get_steps(api, start_time, end_time)

    @tool
    async def get_heart_rate_tool(start_time: str | None = None, end_time: str | None = None) -> dict:
        """Hourly-aggregated heart rate (min/max/avg bpm) within a time range. Defaults to the last 24 hours."""
        return await get_heart_rate(api, start_time, end_time)

    @tool
    async def get_sleep_tool(start_time: str | None = None, end_time: str | None = None) -> dict:
        """Sleep sessions within a time range (defaults to the last 36 hours, covering last night)."""
        return await get_sleep(api, start_time, end_time)

    @tool
    async def get_activity_tool(start_time: str | None = None, end_time: str | None = None) -> dict:
        """Exercise/activity sessions within a time range (defaults to the last 7 days)."""
        return await get_activity(api, start_time, end_time)

    @tool
    async def get_resting_hr_and_hrv_tool(start_date: str | None = None, end_date: str | None = None) -> dict:
        """Daily resting heart rate and heart rate variability (defaults to the last 7 days)."""
        return await get_resting_hr_and_hrv(api, start_date, end_date)

    return [
        get_current_time_tool,
        get_steps_tool,
        get_heart_rate_tool,
        get_sleep_tool,
        get_activity_tool,
        get_resting_hr_and_hrv_tool,
    ]
