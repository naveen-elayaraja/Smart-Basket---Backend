
import os

import httpx
from dotenv import load_dotenv

load_dotenv()

ESP32_BASE_URL = os.getenv("ESP32_BASE_URL", "").rstrip("/")
ESP32_TIMEOUT = 3.0


def send_servo_command(action: str, servo: int = 1) -> dict:
    if action not in {"open", "close"}:
        raise ValueError("Action must be 'open' or 'close'")

    if servo not in {1, 2, 3}:
        raise ValueError("Servo must be 1, 2, or 3")

    if not ESP32_BASE_URL:
        raise RuntimeError("ESP32_BASE_URL is not configured")

    url = f"{ESP32_BASE_URL}/servo/{action}"

    try:
        response = httpx.get(
            url,
            params={"servo": servo},
            timeout=ESP32_TIMEOUT,
        )
        response.raise_for_status()
        result = response.json()

    except httpx.TimeoutException as exc:
        raise RuntimeError("ESP32 request timed out") from exc
    except httpx.RequestError as exc:
        raise RuntimeError("Could not connect to ESP32") from exc
    except ValueError as exc:
        raise RuntimeError("ESP32 returned invalid JSON") from exc

    if result.get("status") != "ok" or result.get("action") != action:
        raise RuntimeError("ESP32 did not confirm the servo command")

    return result
