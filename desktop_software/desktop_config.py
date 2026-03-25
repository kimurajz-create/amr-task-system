# ⚠️ 已棄用（Deprecated）
# 本檔案原本負責讀取 config.json（固定 inner.json）
# 目前系統已改為由 MainWindow 動態載入 configs/inner.json / outer.json
# 並透過 self.config 管理所有設定
#
# ❌ 請勿再 import 以下變數（會導致環境切換失效）
# DB_CONFIG, MIR_IP, USER_LOCATION_MAP, USER_MISSION_GROUP_MAP,
# REQUIRED_MISSION_CODES, SOUND, ROOM_ID_MAP, POLL_INTERVAL, room_id
#
# ✔ 若需使用設定，請改用：
# self.config["XXX"]
#
# 未來可考慮刪除本檔案或僅保留工具函式

import json
import os
import sys

# 檢查執行環境，並且回傳對應的 BASE_DIR
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

CONFIG_PATH = os.path.join(BASE_DIR, "configs", "inner.json")

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

USER_LOCATION_MAP = CONFIG["USER_LOCATION_MAP"]

USER_MISSION_GROUP_MAP = CONFIG["USER_MISSION_GROUP_MAP"]

REQUIRED_MISSION_CODES = set(CONFIG["REQUIRED_MISSION_CODES"])

ENV = CONFIG["ENV"]

EXPECTED_DB_HOST = CONFIG["EXPECTED_DB_HOST"]

SOUND = CONFIG["SOUND"]

ROOM_ID_MAP = CONFIG["ROOM_ID_MAP"]


  