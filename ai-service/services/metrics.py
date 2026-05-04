import time

START_TIME = time.time()
TOTAL_RESPONSE_TIME_MS = 0.0
TOTAL_AI_REQUESTS = 0


def record_ai_response_time(duration_seconds: float) -> None:
    global TOTAL_RESPONSE_TIME_MS, TOTAL_AI_REQUESTS
    TOTAL_RESPONSE_TIME_MS += duration_seconds * 1000.0
    TOTAL_AI_REQUESTS += 1


def get_uptime_seconds() -> float:
    return round(time.time() - START_TIME, 2)


def get_average_response_time_ms() -> float | None:
    if TOTAL_AI_REQUESTS == 0:
        return None
    return round(TOTAL_RESPONSE_TIME_MS / TOTAL_AI_REQUESTS, 2)
