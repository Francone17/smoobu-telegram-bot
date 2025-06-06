import json
import os
from flagsmith import Flagsmith
from flask.cli import load_dotenv

load_dotenv()

flagsmith_key = os.getenv("FLAGSMITH_ENV_KEY")

_flagsmith = Flagsmith(environment_key=flagsmith_key)
_env_flags = _flagsmith.get_environment_flags()

def is_test_mode_enabled():
    return _env_flags.is_feature_enabled("test-mode")

def get_allowed_reservation_ids():
    raw = _env_flags.get_feature_value("allowed-reservation-ids")
    return json.loads(raw or "[]")

def get_blocked_reservation_ids():
    raw = _env_flags.get_feature_value("not-allowed-reservation-ids")
    return json.loads(raw or "[]")
