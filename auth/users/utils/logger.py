import requests
import time
from datetime import datetime
from functools import wraps
from uuid import UUID

LOG_SERVICE_URL = "http://127.0.0.1:8000/logs/"
SERVICE_NAME = "auth"


def make_json_safe(obj):
    if isinstance(obj, UUID):
        return str(obj)
    if isinstance(obj, dict):
        return {k: make_json_safe(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [make_json_safe(v) for v in obj]
    return obj


def log_endpoint(func):
    @wraps(func)
    def wrapper(view, request, *args, **kwargs):
        start_time = time.time()
        log_data = {
            "service": SERVICE_NAME,
            "level": "INFO",
            "endpoint": request.path,
            "method": request.method,
            "message": f"{request.method} {request.path}",
            "response": None,
            "user_id": str(getattr(request.user, "id", "")) if getattr(request.user, "id", None) else None,
            "session_id": str(request.META.get("SESSION_ID", "")) if request.META.get("SESSION_ID", None) else None,
        }

        try:
            if hasattr(request.data, "items"):
                payload = dict(request.data.items())
            else:
                payload = request.data or {}
        except Exception:
            payload = {}

        log_payload = payload.copy()
        for key in ["password", "access", "refresh", "token"]:
            if key in log_payload:
                log_payload[key] = "***"
        log_data["payload"] = log_payload

        try:
            response = func(view, request, *args, **kwargs)

            response_data = getattr(response, "data", None)
            if response_data is None:
                response_data = {"status_code": response.status_code}
            elif not isinstance(response_data, dict):
                response_data = dict(response_data)

            if isinstance(response_data, dict):
                log_response = response_data.copy()
                for key in ["access", "refresh", "token"]:
                    if key in log_response:
                        log_response[key] = "***"
                log_data["response"] = log_response

            client_ip = request.META.get("REMOTE_ADDR", "unknown")
            status_code = getattr(response, "status_code", 0)

            if status_code < 400:
                log_data["level"] = "info"
            elif status_code < 500:
                log_data["level"] = "warning"
            else:
                log_data["level"] = "error"

            log_data["meta"] = f'{client_ip} - "{request.method} {request.path}" {status_code}'
            log_data["duration_ms"] = round((time.time() - start_time) * 1000, 2)
            log_data["timestamp"] = datetime.utcnow().isoformat()

            if not log_data["session_id"]:
                log_data.pop("session_id", None)

            send_log_async(make_json_safe(log_data))  # ✅ безопасно
            return response

        except Exception as e:
            log_data.update({
                "service": SERVICE_NAME,
                "level": "error",
                "message": f"Exception in {request.method} {request.path}: {str(e)}",
                "timestamp": datetime.utcnow().isoformat(),
            })
            send_log_async(make_json_safe(log_data))
            raise e

    return wrapper


def send_log_async(log_data):
    try:
        r = requests.post(LOG_SERVICE_URL, json=log_data, timeout=2)
        if r.status_code != 200:
            print(f"[LOGGER] Log service responded with {r.status_code}: {r.text}")
    except Exception as e:
        print(f"[LOGGER] Failed to send log: {e}")
