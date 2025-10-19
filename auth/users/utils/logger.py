import requests
from datetime import datetime

LOG_SERVICE_URL = "http://127.0.0.1:8000/logs"

def log_endpoint(func):
    def wrapper(view, request, *args, **kwargs):
        response = func(view, request, *args, **kwargs)

        try:
            payload = request.data
            if hasattr(payload, "dict"):
                payload = payload.dict()
            elif not isinstance(payload, dict):
                payload = dict(payload)
        except Exception:
            payload = {}
            
        if "password" in payload:
            payload["password"] = "***"

        try:
            response_data = getattr(response, "data", None)
            if response_data is None:
                response_data = {"status_code": response.status_code}
            elif not isinstance(response_data, dict):
                response_data = dict(response_data)
        except Exception:
            response_data = {"status_code": response.status_code}

        user_id = str(request.user.id) if hasattr(request, "user") and request.user.is_authenticated else None
        session_id = getattr(request.session, "session_key", None)

        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "endpoint": request.path,
            "payload": payload,
            "response": response_data,
            "status": "success" if response.status_code < 400 else "error",
            "user_id": user_id,
            "session_id": session_id
        }

        try:
            r = requests.post(LOG_SERVICE_URL, json=log_data, timeout=2)
            if r.status_code != 200:
                print("Log service returned error:", r.text)
        except Exception as e:
            print("Failed to send log:", e)

        return response

    return wrapper
