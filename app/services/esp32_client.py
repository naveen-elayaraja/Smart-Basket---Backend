
import os

import httpx
from dotenv import load_dotenv

load_dotenv()

ESP32_BASE_URL = os.getenv("ESP32_BASE_URL", "").rstrip("/")
ESP32_TIMEOUT = 3.0


def _send_command(url: str, params: dict | None = None) -> dict:
    try:
        response = httpx.get(
            url,
            params=params,
            timeout=ESP32_TIMEOUT,
        )
        response.raise_for_status()
        result = response.json()

    except httpx.TimeoutException as exc:
        raise RuntimeError(
            f"ESP32 timeout: {type(exc).__name__}: {exc}"
        ) from exc
    except httpx.RequestError as exc:
        raise RuntimeError(
            f"ESP32 request failed: {type(exc).__name__}: {exc}"
        ) from exc
    except ValueError as exc:
        raise RuntimeError("ESP32 returned invalid JSON") from exc

    return result


def send_servo_command(action: str, servo: int = 1) -> dict:
    if action not in {"open", "close"}:
        raise ValueError("Action must be 'open' or 'close'")

    if servo not in {1, 2, 3, 4}:
        raise ValueError("Servo must be 1, 2, 3, or 4")

    if not ESP32_BASE_URL:
        raise RuntimeError("ESP32_BASE_URL is not configured")

    result = _send_command(
        f"{ESP32_BASE_URL}/servo/{action}",
        params={"servo": servo},
    )

    if (
        result.get("status") != "ok"
        or result.get("action") != action
        or result.get("servo") != servo
    ):
        raise RuntimeError("ESP32 did not confirm the servo command")

    return result


def send_all_servos_command(action: str) -> dict:
    if action not in {"open", "close"}:
        raise ValueError("Action must be 'open' or 'close'")

    if not ESP32_BASE_URL:
        raise RuntimeError("ESP32_BASE_URL is not configured")

    endpoint = "open-all" if action == "open" else "close-all"
    expected_action = f"{action}_all"

    result = _send_command(
        f"{ESP32_BASE_URL}/servos/{endpoint}"
    )

    if (
        result.get("status") != "ok"
        or result.get("action") != expected_action
        or result.get("servos") != 4
    ):
        raise RuntimeError(
            "ESP32 did not confirm the command for all four servos"
        )

    return result
