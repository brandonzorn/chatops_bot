import random

from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse
import time

app = FastAPI()

HTTP_CODES = [
    "200 OK",
    "201 Created",
    "200 OK",
    "200 OK",
    "200 OK",
    "201 Created",
    "200 OK",
    "200 OK",
    "204 No Content",
    "301 Moved Permanently",
    "400 Bad Request",
    "500 Internal Server Error",
]

APPS = [
    "Payment API",
    "Billing Engine",
    "Notification Dispatcher",
    "Email Sender",
    "SMS Gateway",
    "chat_ops",
]

def generate_random_logs(count=100, max_minutes_ago=15):
    now_ns = int(time.time() * 1e9)
    logs = []
    for _ in range(count):
        offset_sec = random.randint(0, max_minutes_ago * 60)
        timestamp_ns = now_ns - (offset_sec * int(1e9))
        app_name = random.choice(APPS)
        code = random.choice(HTTP_CODES)
        level = random.choice(["INFO", "WARN", "ERROR"])
        method = random.choice(["GET", "POST", "PUT", "DELETE"])
        path = random.choice(["/login", "/logout", "/checkout", "/items", "/status"])
        message = f'{level} {method} {path} HTTP/1.1 {code}'

        logs.append({
            "timestamp": str(timestamp_ns),
            "line": message,
            "app": app_name
        })
    return sorted(logs, key=lambda x: int(x["timestamp"]), reverse=True)


@app.get("/loki/api/v1/query_range")
def mock_query_range(
    query: str = Query(...),
    start: int = Query(...),  # наносекунды
    end: int = Query(...),
    step: str = Query(...)
):
    logs = generate_random_logs()

    app_name = None
    if 'app="' in query:
        try:
            app_name = query.split('app="')[1].split('"')[0]
        except IndexError:
            pass

    filtered = [
        (log["timestamp"], log["line"]) for log in logs
        if start <= int(log["timestamp"]) <= end and (app_name is None or log["app"] == app_name)
    ]

    response_data = {
        "status": "success",
        "data": {
            "resultType": "streams",
            "result": [
                {
                    "stream": {"app": app_name or "all_apps"},
                    "values": filtered
                }
            ]
        }
    }
    return JSONResponse(content=response_data)
