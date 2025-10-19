import requests
import time
from datetime import datetime
from functools import wraps

LOG_SERVICE_URL = "http://127.0.0.1:8000/logs"
SERVICE_NAME = "auth" 


def log_endpoint(func):
    @wraps(func)
    def wrapper(view, request, *args, **kwargs):
        start_time = time.time()
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "service": SERVICE_NAME,
            "endpoint": request.path,
            "method": request.method,
            "level": "info",
            "status": "pending",
            "duration_ms": None,
            "payload": {},
            "response": {},
            "user_id": None,
            "session_id": None,
        }

        try:
            if hasattr(request.data, "items"):
                payload = {k: v for k, v in request.data.items()}
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
            duration = (time.time() - start_time) * 1000

            try:
                response_data = getattr(response, "data", None)
                if response_data is None:
                    response_data = {"status_code": response.status_code}
                elif not isinstance(response_data, dict):
                    response_data = dict(response_data)
            except Exception:
                response_data = {"status_code": getattr(response, "status_code", None)}
                
            if isinstance(response_data, dict):
                log_response = response_data.copy()
                for key in ["access", "refresh", "token"]:
                    if key in log_response:
                        log_response[key] = "***"
                log_data["response"] = log_response


            log_data.update({
                "timestamp": datetime.utcnow().isoformat(),
                "status": "success" if response.status_code < 400 else "error",
                "level": "info" if response.status_code < 400 else "warning",
                "response": log_data["response"],
                "duration_ms": round(duration, 2),
                "user_id": str(request.user.id) if hasattr(request, "user") and request.user.is_authenticated else None,
                "session_id": getattr(request.session, "session_key", None)
            })

            send_log_async(log_data)
            return response

        except Exception as e:
            duration = (time.time() - start_time) * 1000
            log_data.update({
                "timestamp": datetime.utcnow().isoformat(),
                "status": "error",
                "level": "error",
                "duration_ms": round(duration, 2),
                "response": {"error_message": str(e)},
                "user_id": str(request.user.id) if hasattr(request, "user") and request.user.is_authenticated else None,
                "session_id": getattr(request.session, "session_key", None)
            })
            send_log_async(log_data)
            raise e  
    return wrapper


def send_log_async(log_data):
    try:
        r = requests.post(LOG_SERVICE_URL, json=log_data, timeout=2)
        if r.status_code != 200:
            print(f"[LOGGER] Log service responded with {r.status_code}: {r.text}")
    except Exception as e:
        print(f"[LOGGER] Failed to send log: {e}")
