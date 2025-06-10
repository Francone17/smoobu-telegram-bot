import json
import os
from flagsmith import Flagsmith
from flask.cli import load_dotenv

load_dotenv()

flagsmith_key = os.getenv("FLAGSMITH_ENV_KEY")

_flagsmith = Flagsmith(environment_key=flagsmith_key)
_env_flags = _flagsmith.get_environment_flags()

def is_test_mode_enabled():
    try:
        print("[INFO] Checking 'test-mode' feature flag...")
        print(_env_flags.is_feature_enabled("test-mode"))
        return _env_flags.is_feature_enabled("test-mode")
    except Exception as e:
        print(f"[WARN] Failed to read 'test-mode' flag: {e}")
        return False

def get_allowed_reservation_ids():
    raw = _env_flags.get_feature_value("allowed-reservation-ids")
    return json.loads(raw or "[]")

def get_blocked_reservation_ids():
    raw = _env_flags.get_feature_value("not-allowed-reservation-ids")
    return json.loads(raw or "[]")

def get_human_resolved_complaint_ids():
    raw = _env_flags.get_feature_value("human-resolved-complaint-ids")
    return json.loads(raw or "[]")
