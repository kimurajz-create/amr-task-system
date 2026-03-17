import json
import os

import sys

if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

CONFIG_PATH = os.path.join(BASE_DIR, "config.json")

def load_config():
    if not os.path.exists(CONFIG_PATH):
        raise FileNotFoundError("config.json not found: {CONFIG_PATH}")

    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

CONFIG = load_config()

room_id = CONFIG["ROOM_ID"]
POLL_INTERVAL = CONFIG["POLL_INTERVAL"]


MIR_IP = CONFIG["MIR_IP"]

DB_CONFIG = CONFIG["DB_CONFIG"]

ROOM_ID_MAP = CONFIG["ROOM_ID_MAP"]

USER_LOCATION_MAP = CONFIG["USER_LOCATION_MAP"]

USER_MISSION_GROUP_MAP = CONFIG["USER_MISSION_GROUP_MAP"]

REQUIRED_MISSION_CODES = set(CONFIG["REQUIRED_MISSION_CODES"])

ENV = CONFIG["ENV"]

EXPECTED_DB_HOST = CONFIG["EXPECTED_DB_HOST"]