import re
import httpx
from datetime import datetime, timedelta

from config import GRAFANA_URL
from models import Service

STEP = "1m"


def get_time_range(minutes=10):
    end = datetime.now()
    start = end - timedelta(minutes=minutes)
    return (
        int(start.timestamp() * 1e9),
        int(end.timestamp() * 1e9),
    )


def parse_logs(data):
    total = 0
    error_count = 0
    error_pattern = re.compile(r"\bHTTP/[\d.]+\s+(4\d{2}|5\d{2})\b")

    for result in data["data"]["result"]:
        for _, log_line in result["values"]:
            total += 1
            if error_pattern.search(log_line):
                error_count += 1

    return error_count, total


async def check_service(service: Service):
    start, end = get_time_range(minutes=10)

    params = {
        "query": f'{{app="{service.name}"}}',
        "start": start,
        "end": end,
        "step": STEP,
    }

    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(
            f"{GRAFANA_URL}/loki/api/v1/query_range",
            params=params,
        )
        response.raise_for_status()
        data = response.json()

    errors, total = parse_logs(data)

    if total == 0:
        return 0
    return int((errors / total) * 100)


__all__ = [
    "check_service",
]
