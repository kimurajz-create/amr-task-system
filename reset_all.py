import json
import sys
import time
import csv
import math
from datetime import datetime
from pathlib import Path
import requests

# ---------------------------------------------------------------------------
# 設定 MiR 機器人資訊與參數
# ---------------------------------------------------------------------------
MIR_IP = "192.168.12.20"  # 請改為您的 MiR IP
API_URL = f"http://{MIR_IP}/api/v2.0"

# Header 設定 (請替換為您系統的 Base64 認證金鑰)
HEADERS = {
    "Content-Type": "application/json",
    "Authorization": "Basic ZGlzdHJpYnV0b3I6NjJmMmYwZjFlZmYxMGQzMTUyYzk1ZjZmMDU5NjU3NmU0ODJiYjhlNDQ4MDY0MzNmNGNmOTI5NzkyODM0YjAxNA==",
    "Accept-Language": "en-US",
}

REQUEST_TIMEOUT = 5
MONITOR_INTERVAL_SECONDS = 2
SHELF_UNLOAD_TIMEOUT_SECONDS = 300
# 步驟 5 前回充：急停解除後才派送，最多等這麼久。
ESTOP_CLEAR_WAIT_SECONDS = 120
TASK_METRICS_FILE = Path(__file__).with_name("mir_task_metrics.csv")

# 依 MiR API 文件：PUT /status 可設 Ready=3、Pause=4、Manual control=11；
# GET /status 的執行中、急停、錯誤狀態分別為 5、10、12。
STATE_ID_READY = 3
STATE_ID_PAUSE = 4
STATE_ID_EXECUTING = 5
STATE_ID_EMERGENCY_STOP = 10
STATE_ID_ERROR = 12

# 車頂頂升柱：與主程式 set_lift_position(False) 相同，internal IO 先關上升再開下降。
# 載運任務會等 Internal I/O input 3 從 off 變 on，那個回授代表頂升柱已到頂。
TOP_LIFT_IO_GUID = "mirconst-guid-0000-0001-internalIO00"
TOP_LIFT_DOWN_PORT = 2
TOP_LIFT_UP_PORT = 3
TOP_LIFT_UP_INPUT = 3
LIFT_DOWN_MIN_SECONDS = 8
LIFT_DOWN_TIMEOUT_SECONDS = 25
LIFT_POLL_SECONDS = 0.5
# 0.7 公尺還停在貨架內。倒車加倍，並等實際位移接近這段距離才算離開。
SHELF_EXIT_DISTANCE_M = 1.4
SHELF_EXIT_CLEAR_M = 1.2
SHELF_EXIT_TIMEOUT_SECONDS = 40
MOVE_TO_TARGET_MISSION_NAME = "MoveToTarget_Critical"
# 空車時 GET /status 的長方形對得上 MiR250 Dynamic，不是 shelf carrier base。
NARROW_FOOTPRINT_NAME = "MiR250 Dynamic"
# 載貨架時的八邊形最接近這筆。Shelf_Army_Hospital 是另一個小長方形。
WIDE_FOOTPRINT_NAME = "MIR250 MK2 shelf carrier base 0703"
CART_TRANSPORT_MISSION_NAME = "Taichung Military Hospital Cart Transport"
FOOTPRINT_SWITCH_TIMEOUT_SECONDS = 20
SET_FOOTPRINT_ACTION_TYPE = "set_footprint"
SET_FOOTPRINT_PARAMETER_ID = "footprint"
CHARGE_MISSION_NAME = "Charge"
# 公司這台車的驗證任務：Place 放下貨架並倒車，接著開回公司充電樁。
COMPANY_PLACE_AND_CHARGE_MISSION_NAME = "James_Reset_All"
COMPANY_CHARGE_POSITION_NAME = "LbV2_MiR Charge 48V V2"
HOSPITAL_CHARGE_POSITION_NAME = "MH_MiR Charge 48V 35A OA"
# 對應「立即返回充電」：優先用已知充電樁名稱，否則找名稱含 Charge 的位置。
CHARGE_POSITION_NAME_CANDIDATES = (
    COMPANY_CHARGE_POSITION_NAME,
    HOSPITAL_CHARGE_POSITION_NAME,
)
DOCK_TO_TARGET_MISSION_NAME = "DockToTarget_Critical"


def pause_robot(reason):
    """中止 Reset。不把 MiR Status 設成 Pause，否則後續任務無法執行。"""
    print(f"  -> {reason}。已停止 Reset，MiR Status 維持不變。")


def get_distance_m(status_data):
    """讀取正式 GetStatus 文件列出的 moved 欄位。"""
    try:
        moved = status_data.get("moved")
        return float(moved) if moved is not None else None
    except (TypeError, ValueError):
        return None


def get_mission_queue_entry(queue_id, mission_id):
    """取得本次任務的佇列項目；POST 未提供 ID 時從 queue 反查。"""
    if queue_id is not None:
        response = requests.get(
            f"{API_URL}/mission_queue/{queue_id}", headers=HEADERS,
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        return response.json()

    response = requests.get(
        f"{API_URL}/mission_queue", headers=HEADERS, timeout=REQUEST_TIMEOUT
    )
    response.raise_for_status()
    entries = response.json()
    matches = [entry for entry in entries if entry.get("mission_id") == mission_id]
    return max(matches, key=lambda entry: entry.get("id", 0)) if matches else None


def parse_api_timestamp(value):
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None


def append_task_metrics(record):
    """將任務執行結果與時間、里程差追加至 CSV。"""
    fields = [
        "mission_name", "mission_id", "queue_id", "result",
        "started_at", "finished_at", "duration_seconds",
        "distance_start_m", "distance_end_m", "distance_traveled_m",
    ]
    write_header = not TASK_METRICS_FILE.exists()
    with TASK_METRICS_FILE.open("a", newline="", encoding="utf-8-sig") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fields)
        if write_header:
            writer.writeheader()
        writer.writerow({key: record.get(key) for key in fields})
    print(f"  -> 任務紀錄已寫入：{TASK_METRICS_FILE}")


def show_task_metrics():
    """顯示已記錄的任務耗時、行走距離及成功任務統計。"""
    if not TASK_METRICS_FILE.exists():
        print(f"目前沒有任務紀錄：{TASK_METRICS_FILE}")
        return

    try:
        with TASK_METRICS_FILE.open("r", newline="", encoding="utf-8-sig") as csv_file:
            records = list(csv.DictReader(csv_file))
    except (OSError, csv.Error) as exc:
        print(f"讀取任務紀錄失敗：{exc}")
        return

    if not records:
        print("任務紀錄檔目前沒有資料。")
        return

    def format_value(value, suffix):
        try:
            return f"{float(value):.2f} {suffix}"
        except (TypeError, ValueError):
            return "未記錄"

    print("\n=== MiR 任務時間與距離紀錄 ===")
    for index, record in enumerate(records, start=1):
        print(
            f"{index}. {record.get('mission_name') or '未命名任務'} "
            f"[Queue {record.get('queue_id') or '-'}] "
            f"結果：{record.get('result') or '未知'}"
        )
        print(f"   開始：{record.get('started_at') or '未記錄'}")
        print(f"   結束：{record.get('finished_at') or '未記錄'}")
        print(f"   耗時：{format_value(record.get('duration_seconds'), '秒')}")
        print(f"   距離：{format_value(record.get('distance_traveled_m'), '公尺')}")

    successful = [record for record in records if (record.get("result") or "").casefold() == "done"]
    total_duration = 0.0
    duration_count = 0
    total_distance = 0.0
    distance_count = 0
    for record in successful:
        try:
            total_duration += float(record.get("duration_seconds"))
            duration_count += 1
        except (TypeError, ValueError):
            pass
        try:
            total_distance += float(record.get("distance_traveled_m"))
            distance_count += 1
        except (TypeError, ValueError):
            pass

    print("\n=== Done 任務統計 ===")
    print(f"完成任務數：{len(successful)}")
    print(f"可用耗時合計：{total_duration:.2f} 秒（{duration_count} 筆有數值）")
    print(f"可用距離合計：{total_distance:.2f} 公尺（{distance_count} 筆有數值）")


def get_mission_queue_entries():
    response = requests.get(
        f"{API_URL}/mission_queue", headers=HEADERS, timeout=REQUEST_TIMEOUT
    )
    response.raise_for_status()
    entries = response.json()
    if not isinstance(entries, list):
        raise ValueError("Mission Queue 回傳格式不是清單")
    return entries


def queue_entry_key(entry, index):
    queue_id = entry.get("id")
    if queue_id is not None:
        return str(queue_id)
    return f"{entry.get('mission_id', 'unknown')}:{entry.get('ordered', index)}"


def is_terminal_queue_state(state):
    return str(state or "").casefold() in {
        "done", "finished", "completed", "succeeded", "success",
        "failed", "aborted", "cancelled", "canceled", "error",
    }


def record_mission_result(entry, tracking, result, end_status):
    """計算單筆任務耗時與累積里程差，印出結果並寫入 CSV。"""
    finished_at = entry.get("finished") or datetime.now().astimezone().isoformat()
    started_at = (tracking or {}).get("started_at") or entry.get("started")
    started_dt = parse_api_timestamp(started_at)
    finished_dt = parse_api_timestamp(finished_at)

    if started_dt and finished_dt:
        try:
            duration_seconds = max(0.0, (finished_dt - started_dt).total_seconds())
        except TypeError:
            duration_seconds = max(
                0.0,
                (finished_dt.replace(tzinfo=None) - started_dt.replace(tzinfo=None)).total_seconds(),
            )
    elif tracking and tracking.get("started_monotonic") is not None:
        duration_seconds = max(0.0, time.monotonic() - tracking["started_monotonic"])
    else:
        duration_seconds = None

    distance_start_m = (tracking or {}).get("distance_start_m")
    distance_end_m = get_distance_m(end_status)
    distance_traveled_m = None
    if distance_start_m is not None and distance_end_m is not None and distance_end_m >= distance_start_m:
        distance_traveled_m = distance_end_m - distance_start_m

    mission_id = entry.get("mission_id")
    record = {
        "mission_name": entry.get("description") or mission_id or "MiR 任務",
        "mission_id": mission_id,
        "queue_id": entry.get("id"),
        "result": result,
        "started_at": started_at,
        "finished_at": finished_at,
        "duration_seconds": duration_seconds,
        "distance_start_m": distance_start_m,
        "distance_end_m": distance_end_m,
        "distance_traveled_m": distance_traveled_m,
    }
    append_task_metrics(record)

    duration_text = f"{duration_seconds:.2f} 秒" if duration_seconds is not None else "未記錄"
    distance_text = f"{distance_traveled_m:.2f} 公尺" if distance_traveled_m is not None else "未記錄（缺少起始或結束里程）"
    print("\n=== 任務執行統計 ===")
    print(f"任務：{record['mission_name']}")
    print(f"Queue ID：{record['queue_id'] or '未提供'}；結果：{result}")
    print(f"開始：{started_at or '未記錄'}")
    print(f"結束：{finished_at}")
    print(f"執行時間：{duration_text}")
    print(f"行走距離：{distance_text}")
    print("====================")


def monitor_all_missions():
    """監看 Mission Queue 中的任務，於每筆任務結束時顯示並保存統計。"""
    try:
        initial_entries = get_mission_queue_entries()
    except (requests.RequestException, ValueError) as exc:
        print(f"無法讀取 Mission Queue，停止監看：{exc}")
        return

    terminal_seen = set()
    tracking = {}
    for index, entry in enumerate(initial_entries):
        key = queue_entry_key(entry, index)
        state = str(entry.get("state", "")).casefold()
        if is_terminal_queue_state(state):
            terminal_seen.add(key)
        elif state == "executing":
            # 監看啟動前已開始的任務，不能把「現在」的里程冒充任務起始里程。
            tracking[key] = {
                "started_at": entry.get("started"),
                "started_monotonic": None,
                "distance_start_m": None,
            }

    print(f"開始監看 MiR 任務，每 1 秒檢查一次；按 Ctrl+C 停止。CSV：{TASK_METRICS_FILE}")
    while True:
        try:
            entries = get_mission_queue_entries()
            current_status = None
            for index, entry in enumerate(entries):
                key = queue_entry_key(entry, index)
                state = str(entry.get("state", "")).casefold()

                if state == "executing" and key not in tracking:
                    if current_status is None:
                        current_status = get_mir_status()
                    tracking[key] = {
                        "started_at": entry.get("started") or datetime.now().astimezone().isoformat(),
                        "started_monotonic": time.monotonic(),
                        "distance_start_m": get_distance_m(current_status),
                    }
                    print(f"偵測到任務開始：{entry.get('description') or entry.get('mission_id')} (Queue {entry.get('id', '?')})")

                elif is_terminal_queue_state(state) and key not in terminal_seen:
                    if current_status is None:
                        current_status = get_mir_status()
                    record_mission_result(entry, tracking.get(key), entry.get("state") or state, current_status)
                    terminal_seen.add(key)
                    tracking.pop(key, None)

            time.sleep(1)
        except requests.RequestException as exc:
            print(f"讀取 MiR 任務狀態失敗，稍後重試：{exc}")
            time.sleep(2)
        except KeyboardInterrupt:
            print("\n已停止任務監看；尚未結束的任務不會記作完成。")
            return


def get_mir_status():
    """取得 AMR 當前狀態資訊"""
    res = requests.get(f"{API_URL}/status", headers=HEADERS, timeout=REQUEST_TIMEOUT)
    res.raise_for_status()
    return res.json()

def get_mission_guid_by_name(mission_name):
    """輸入 Mission 名稱，自動回傳 GUID"""
    res = requests.get(
        f"{API_URL}/missions", headers=HEADERS, timeout=REQUEST_TIMEOUT
    )
    if res.status_code == 200:
        missions = res.json()
        for m in missions:
            # 比對任務名稱 (請注意大小寫需一致)
            if m.get("name") == mission_name:
                print(f"[找到] 任務名稱: {mission_name} -> GUID: {m.get('guid')}")
                return m.get("guid")
    print(f"[失敗] 找不到名稱為 '{mission_name}' 的 Mission")
    return None

def parse_mir_status_for_user(status_data):
    # 讀取 status API
    #status_data = requests.get(f"{API_URL}/status", headers=HEADERS).json()

    state_id = status_data.get("state_id")
    errors = status_data.get("errors", [])

    # 1. 急停判斷
    if state_id == STATE_ID_EMERGENCY_STOP:
        return {
            "level": "DANGER",
            "title": "緊急停止已觸發",
            "action": "請解開車上急停按鈕，並按下 Reset 鈕。",
        }

    # 2. 系統錯誤
    if state_id == STATE_ID_ERROR:
        err_msg = errors[0].get("description") if errors else "未知錯誤"
        return {
            "level": "ERROR",
            "title": f"系統異常: {err_msg}",
            "action": "請排除障礙後執行【一鍵 Reset 重置】。",
        }

    # MiR /status 文件有列出 safety_system_muted；它表示靜音狀態，並非障礙物偵測。
    if status_data.get("safety_system_muted") is True:
        return {
            "level": "WARNING",
            "title": "安全系統處於 Muted",
            "action": "確認現場安全及安全系統設定；Muted 狀態不能用來判斷是否有障礙物。",
        }

    # GetStatus 的 velocity 物件包含 linear (m/s) 與 angular (degrees/s)。
    velocity_data = status_data.get("velocity")
    if isinstance(velocity_data, dict):
        linear_velocity = velocity_data.get("linear")
    else:
        linear_velocity = None
    try:
        is_stopped = linear_velocity is not None and abs(float(linear_velocity)) < 0.001
    except (TypeError, ValueError):
        is_stopped = False

    state_text = str(status_data.get("state_text", "")).casefold()
    is_waiting_or_paused = "wait" in state_text or "pause" in state_text

    if is_stopped and (
        state_id in {STATE_ID_PAUSE, STATE_ID_EXECUTING} or is_waiting_or_paused
    ):
        if state_id == STATE_ID_PAUSE or is_waiting_or_paused:
            return {
                "level": "WARNING",
                "title": "車輛停止／等待中",
                "action": "確認車輛周圍與 MiR 錯誤訊息；目前狀態只能確認車輛停止／等待，不能確認是否為障礙物觸發。",
            }

        return {
            "level": "INFO",
            "title": "車輛已停止",
            "action": "檢查 MiR 狀態訊息與現場狀況，以確認停止原因。",
        }

    # 4. 正常運行或待命
    if state_id == STATE_ID_READY:
        return {"level": "INFO", "title": "車輛待命 mount 中", "action": "無"}

    return {"level": "INFO", "title": "正常運作中", "action": "無"}

def get_precise_error_guidance(status_data, api_url, headers):
    """當 state_id 為 Error (12) 時，讀取詳細 errors 並回傳排除建議。"""
    state_id = status_data.get("state_id")

    if state_id != STATE_ID_ERROR:
        return None

    # 1. 嘗試由 status 中取得 errors 陣列，若無則請求 /errors API
    errors = status_data.get("errors", [])
    if not errors:
        try:
            err_res = requests.get(
                f"{api_url}/errors", headers=headers, timeout=REQUEST_TIMEOUT
            )
            if err_res.status_code == 200:
                errors = err_res.json()
        except Exception:
            pass

    if not errors:
        return {
            "code": 0,
            "title": "系統未知錯誤",
            "action": "無法取得詳細錯誤代碼，請直接執行【一鍵 Reset】重置車輛狀態。",
        }

    # 取得最新的一筆錯誤訊息
    main_error = errors[0]
    err_code = main_error.get("code", 0)
    err_desc = main_error.get("description", "").lower()

    # 2. 根據 Code 與 Description 進行精準條件判定
    if err_code == 11 or "path" in err_desc or "blocked" in err_desc:
        return {
            "code": err_code,
            "title": "路徑阻塞或規劃逾時",
            "action": "請清理車頭與目標點周圍 1 公尺內的雜物或人員，隨後執行【一鍵 Reset】。",
        }

    elif err_code == 1 or "e-stop" in err_desc or "emergency" in err_desc:
        return {
            "code": err_code,
            "title": "急停按鈕已釋放，待軟體復位",
            "action": "請確認急停按鈕已旋開，點擊【一鍵 Reset】即可恢復待命。",
        }

    elif err_code == 40 or "localization" in err_desc or "confidence" in err_desc:
        return {
            "code": err_code,
            "title": "定位信心度過低",
            "action": "若無人車有被手動推移，請推回原位置，或請於車內Dashboard使用手動輔助定位。",
        }

    elif err_code == 80 or "hook" in err_desc or "lift" in err_desc:
        return {
            "code": err_code,
            "title": "Shelf 頂升模組動作異常",
            "action": "請檢查車架是否傾斜卡住機構，排除物理阻礙後執行【一鍵 Reset】。",
        }

    elif err_code == 32 or "dock" in err_desc or "reflector" in err_desc:
        return {
            "code": err_code,
            "title": "站點/充電樁精密對接失敗",
            "action": "請確認站點/充電樁反射板未被搬移、遮擋或髒污，清潔後執行【一鍵 Reset】。",
        }

    elif err_code == 102 or "motor" in err_desc or "encoder" in err_desc:
        return {
            "code": err_code,
            "title": "驅動馬達或車輪過載",
            "action": "請檢查：1. 車架煞車輪是否忘了釋放(鎖死)？ 2. 車輪是否卡異物？，排除後執行【一鍵 Reset】。",
        }

    # 預設通用建議
    return {
        "code": err_code,
        "title": f"系統錯誤 ({main_error.get('description', '無詳細說明')})",
        "action": "請檢查車輛周圍安全狀況後，執行【一鍵 Reset】嘗試復位。",
    }


def get_status_guidance(status_data):
    """合併狀態判斷與錯誤細節，提供監控畫面使用。"""
    guidance = get_precise_error_guidance(status_data, API_URL, HEADERS)
    if guidance:
        guidance["level"] = "ERROR"
        return guidance
    return parse_mir_status_for_user(status_data)


def monitor_mir():
    """持續讀取 AMR 狀態；狀態或建議改變時顯示一次。Ctrl+C 可結束。"""
    print(f"開始監控 MiR ({MIR_IP})，每 {MONITOR_INTERVAL_SECONDS} 秒更新；按 Ctrl+C 結束。")
    previous = None
    while True:
        try:
            status = get_mir_status()
            guidance = get_status_guidance(status)
            signature = (guidance.get("level"), guidance.get("title"), guidance.get("action"))
            if signature != previous:
                print(f"\n[{datetime.now():%Y-%m-%d %H:%M:%S}] [{guidance.get('level')}] {guidance.get('title')}")
                print(f"建議措施：{guidance.get('action', '無')}")
                previous = signature
        except requests.RequestException as exc:
            signature = ("CONNECTION_ERROR", str(exc))
            if signature != previous:
                print(f"\n[{datetime.now():%Y-%m-%d %H:%M:%S}] [連線異常] 無法取得 AMR 狀態：{exc}")
                print("建議措施：確認 AMR 電源、網路連線、IP 設定及 API 權限。")
                previous = signature
        except (ValueError, TypeError) as exc:
            print(f"\n[{datetime.now():%Y-%m-%d %H:%M:%S}] [資料異常] 狀態資料格式無法解析：{exc}")
        time.sleep(MONITOR_INTERVAL_SECONDS)

def shelf_exit_pose(x, y, orientation_deg, distance_m):
    """沿車頭反方向退 distance_m。MiR orientation 0 度朝 +X，逆時針為正。"""
    radians = math.radians(float(orientation_deg))
    return (
        float(x) - math.cos(radians) * distance_m,
        float(y) - math.sin(radians) * distance_m,
        float(orientation_deg),
    )


def lift_output_is_on(payload, port):
    """從 io_modules 回傳裡讀指定 output。找不到回傳 None。"""
    points = []
    if isinstance(payload, dict):
        outputs = payload.get("outputs")
        if isinstance(outputs, list):
            points.extend(outputs)
    return _lift_point_is_on(points, port)


def lift_input_is_on(payload, port):
    """從 io_modules 回傳裡讀指定 input。找不到回傳 None。"""
    points = []
    if isinstance(payload, dict):
        inputs = payload.get("inputs")
        if isinstance(inputs, list):
            points.extend(inputs)
    elif isinstance(payload, list):
        points.extend(payload)
    return _lift_point_is_on(points, port)


def _lift_point_is_on(points, port):

    for item in points:
        if not isinstance(item, dict):
            continue
        ident = item.get("id", item.get("index", item.get("port")))
        name = str(item.get("name") or "").strip()
        matched = name == str(port)
        if not matched:
            try:
                matched = int(ident) == port
            except (TypeError, ValueError):
                matched = False
        if not matched:
            continue
        value = item.get("value", item.get("on", item.get("state")))
        if isinstance(value, str):
            return value.strip().lower() in ("1", "true", "on")
        return bool(value)
    return None


def status_is_protective_stop(status_data):
    """急停、錯誤，或文字裡出現 protective stop。

    不用單獨比對 protective，避免 ReduceProtectiveFieldAction 被誤判。
    """
    if not isinstance(status_data, dict):
        return False
    if status_data.get("state_id") in (STATE_ID_EMERGENCY_STOP, STATE_ID_ERROR):
        return True
    texts = [
        status_data.get("state_text"),
        status_data.get("mission_text"),
    ]
    errors = status_data.get("errors") or []
    if isinstance(errors, list):
        for error in errors:
            if isinstance(error, dict):
                texts.append(error.get("description"))
                texts.append(error.get("error_human"))
    combined = " ".join(str(text) for text in texts if text).lower()
    return "protective stop" in combined


def wait_until_robot_can_run_mission(timeout_seconds=ESTOP_CLEAR_WAIT_SECONDS):
    """等急停/錯誤解除；等待期間會重送 clear_error。"""
    deadline = time.monotonic() + timeout_seconds
    last_clear_at = 0.0
    announced = False
    while time.monotonic() < deadline:
        try:
            status = get_mir_status()
        except requests.RequestException as exc:
            print(f"  -> 等待可執行狀態時讀取失敗：{exc}")
            time.sleep(LIFT_POLL_SECONDS)
            continue

        if not status_is_protective_stop(status):
            if status.get("state_id") in (STATE_ID_READY, STATE_ID_EXECUTING):
                if announced:
                    print("  -> 急停/錯誤已解除，可繼續派送任務。")
                return True
            response = requests.put(
                f"{API_URL}/status",
                json={"state_id": STATE_ID_READY},
                headers=HEADERS,
                timeout=REQUEST_TIMEOUT,
            )
            if response.status_code == 200:
                if announced:
                    print("  -> 急停/錯誤已解除，已切到 Ready。")
                return True

        now = time.monotonic()
        if now - last_clear_at >= 2.0:
            if not announced:
                print(
                    f"  -> 偵測到急停或錯誤，最多等待 {timeout_seconds} 秒；"
                    "請解除急停，期間會重送 clear_error..."
                )
                announced = True
            clear_robot_error()
            last_clear_at = now
        time.sleep(LIFT_POLL_SECONDS)

    print(f"  -> [失敗] {timeout_seconds} 秒內急停或錯誤沒有解除。")
    return False


def _set_lift_output(port, on, announce=True):
    url = f"{API_URL}/io_modules/{TOP_LIFT_IO_GUID}/status"
    response = requests.put(
        url,
        json={"port": port, "on": on, "timeout": 0},
        headers=HEADERS,
        timeout=REQUEST_TIMEOUT,
    )
    if response.status_code != 200:
        print(
            f"  -> [失敗] Top Lift port {port} 設定失敗："
            f"{response.status_code} {response.text}"
        )
        return False
    if announce:
        print(f"  -> Top Lift port {port} 設為 {on}")
    return True


def command_lift_down(announce=True):
    """先關上升腳位 3，再開下降腳位 2。"""
    if not _set_lift_output(TOP_LIFT_UP_PORT, False, announce=announce):
        return False
    time.sleep(0.2)
    return _set_lift_output(TOP_LIFT_DOWN_PORT, True, announce=announce)


def read_lift_up_input(announce=True):
    """讀上升到位回授。讀不到不中止 Reset，回傳 None。"""
    try:
        response = requests.get(
            f"{API_URL}/io_modules/{TOP_LIFT_IO_GUID}",
            headers=HEADERS,
            timeout=REQUEST_TIMEOUT,
        )
    except requests.RequestException as exc:
        if announce:
            print(f"  -> 讀取頂升柱回授失敗：{exc}")
        return None
    if response.status_code != 200:
        if announce:
            print(
                f"  -> 讀取頂升柱回授失敗：{response.status_code} {response.text}"
            )
        return None
    try:
        return lift_input_is_on(response.json(), TOP_LIFT_UP_INPUT)
    except ValueError as exc:
        if announce:
            print(f"  -> 頂升柱回授內容無法解析：{exc}")
        return None


def clear_robot_error():
    response = requests.put(
        f"{API_URL}/status",
        json={"clear_error": True},
        headers=HEADERS,
        timeout=REQUEST_TIMEOUT,
    )
    if response.status_code != 200:
        print(
            f"  -> [失敗] clear_error 失敗："
            f"{response.status_code} {response.text}"
        )
        return False
    return True


def delete_mission_queue():
    response = requests.delete(
        f"{API_URL}/mission_queue", headers=HEADERS, timeout=REQUEST_TIMEOUT
    )
    if response.status_code == 204:
        return True
    print(
        f"  -> [失敗] 清除任務佇列未成功 (Status: {response.status_code}): {response.text}"
    )
    return False


def lower_top_lift_fully():
    """降下頂升柱並等到坐穩。保護性停止時先清掉載運任務，再清除錯誤並繼續降。"""
    started = time.monotonic()
    deadline = started + LIFT_DOWN_TIMEOUT_SECONDS
    sensor_seen = False
    released_up_input = False
    announced = False
    announced_sensor_error = False
    cleared_queue_after_stop = False
    while time.monotonic() < deadline:
        if not command_lift_down(announce=not announced):
            return False
        announced = True
        status = get_mir_status()
        if status_is_protective_stop(status):
            if not cleared_queue_after_stop:
                print(
                    "  -> 降下時出現保護性停止。"
                    "先清空任務佇列，避免載運繼續開往目的地。"
                )
                if not delete_mission_queue():
                    return False
                print("  -> 已清空任務佇列，清除錯誤後繼續降下頂升柱。")
                cleared_queue_after_stop = True
            if not clear_robot_error():
                return False
            time.sleep(LIFT_POLL_SECONDS)
            continue
        up_input = read_lift_up_input(announce=not announced_sensor_error)
        announced_sensor_error = True
        if up_input is not None:
            sensor_seen = True
        if up_input is False:
            released_up_input = True
        elapsed = time.monotonic() - started
        if elapsed >= LIFT_DOWN_MIN_SECONDS and released_up_input:
            print(
                f"  -> 上升回授 input {TOP_LIFT_UP_INPUT} 已關閉，"
                f"且已持續降下 {elapsed:.1f} 秒，頂升柱已降到底。"
            )
            return True
        if elapsed >= LIFT_DOWN_MIN_SECONDS and up_input is None and not sensor_seen:
            print(
                f"  -> 讀不到上升回授。已持續降下 {elapsed:.1f} 秒，"
                "依行程時間視為頂升柱已降到底。"
            )
            return True
        time.sleep(LIFT_POLL_SECONDS)

    print(
        f"  -> [失敗] {LIFT_DOWN_TIMEOUT_SECONDS} 秒內頂升柱沒有降到底，"
        "不倒車、不回充。"
    )
    return False


def parse_footprint_polygon(value):
    """把 footprint 字串或點列轉成可比對的座標。格式不符回傳 None。"""
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return None
        try:
            value = json.loads(text)
        except json.JSONDecodeError:
            return None
    if not isinstance(value, list) or len(value) < 3:
        return None
    points = []
    for point in value:
        if not isinstance(point, (list, tuple)) or len(point) < 2:
            return None
        try:
            points.append((round(float(point[0]), 3), round(float(point[1]), 3)))
        except (TypeError, ValueError):
            return None
    return points


def footprints_match(current, candidate):
    current_points = parse_footprint_polygon(current)
    candidate_points = parse_footprint_polygon(candidate)
    if not current_points or not candidate_points:
        return False
    return current_points == candidate_points


def choose_footprint_by_name(footprints, footprint_name):
    if not isinstance(footprints, list):
        return None
    target_name = str(footprint_name or "").strip().lower()
    for item in footprints:
        if not isinstance(item, dict):
            continue
        if str(item.get("name") or "").strip().lower() == target_name:
            return item
    return None


def choose_narrow_footprint(footprints):
    """窄外形是空車時 status 上的長方形，名稱是 MiR250 Dynamic。"""
    return choose_footprint_by_name(footprints, NARROW_FOOTPRINT_NAME)


def parse_action_parameters(action):
    if not isinstance(action, dict):
        return []
    parameters = action.get("parameters")
    if isinstance(parameters, str):
        try:
            parameters = json.loads(parameters)
        except ValueError:
            return []
    if not isinstance(parameters, list):
        return []
    return [item for item in parameters if isinstance(item, dict)]


def choose_set_footprint_action(actions):
    """從任務動作裡找出 Set footprint。這台車只能靠這個動作切換目前外形。"""
    if not isinstance(actions, list):
        return None
    for action in actions:
        if not isinstance(action, dict):
            continue
        if "footprint" in str(action.get("action_type") or "").lower():
            return action
    return None


def footprint_parameter_id(action):
    for item in parse_action_parameters(action):
        parameter_id = str(item.get("id") or "")
        if "footprint" in parameter_id.lower():
            return parameter_id
    return SET_FOOTPRINT_PARAMETER_ID


def footprint_action_value(example_action, footprint):
    """沿用載運任務參數的寫法。對方用網址就送網址，否則送 guid。"""
    guid = str((footprint or {}).get("guid") or "")
    url = str((footprint or {}).get("url") or "")
    if guid and not url:
        url = f"/v2.0.0/footprints/{guid}"
    if not isinstance(example_action, dict):
        return guid or url
    for item in parse_action_parameters(example_action):
        if "footprint" not in str(item.get("id") or "").lower():
            continue
        example_value = str(item.get("value") or "")
        if example_value.startswith("/"):
            return url or guid
        return guid or url
    return guid or url


def build_set_footprint_action(action_type, parameter_id, footprint_value, mission_id):
    return {
        "action_type": action_type,
        "mission_id": mission_id,
        "parameters": [{"id": parameter_id, "value": footprint_value}],
        "priority": 1,
    }


def clear_mission_queue():
    print("清空任務佇列...")
    if delete_mission_queue():
        print("  -> 任務佇列已順利清空。")
        return True
    return False


def find_relative_move_mission_id():
    response = requests.get(
        f"{API_URL}/missions", headers=HEADERS, timeout=REQUEST_TIMEOUT
    )
    if response.status_code != 200:
        print(f"  -> 讀取任務清單失敗：{response.status_code} {response.text}")
        return None
    missions = response.json()
    if not isinstance(missions, list):
        return None
    for mission in missions:
        if not isinstance(mission, dict):
            continue
        name = str(mission.get("name") or "")
        if "relative" in name.lower():
            mission_id = mission.get("guid") or mission.get("id")
            print(f"  -> 使用相對移動任務: {name} -> {mission_id}")
            return mission_id
    return None


def post_relative_shelf_exit(mission_id):
    payload = {
        "mission_id": mission_id,
        "parameters": [
            {"id": "x", "value": -SHELF_EXIT_DISTANCE_M},
            {"id": "y", "value": 0},
            {"id": "ori", "value": 0},
        ],
    }
    response = requests.post(
        f"{API_URL}/mission_queue",
        json=payload,
        headers=HEADERS,
        timeout=REQUEST_TIMEOUT,
    )
    if response.status_code == 201:
        print(f"  -> 已派送倒車 {SHELF_EXIT_DISTANCE_M:.2f} 公尺。")
        return True
    print(f"  -> 相對移動任務失敗：{response.status_code} {response.text}")
    return False


def post_backoff_position_move(status):
    """沒有相對移動任務時，在車後建立暫時點，再用 MoveToTarget_Critical 過去。"""
    position = status.get("position") if isinstance(status, dict) else None
    map_id = status.get("map_id") if isinstance(status, dict) else None
    if not isinstance(position, dict) or not map_id:
        print("  -> [失敗] 無法取得目前座標或 map_id，不能倒車離開貨架。")
        return None
    try:
        exit_x, exit_y, exit_orientation = shelf_exit_pose(
            position["x"],
            position["y"],
            position["orientation"],
            SHELF_EXIT_DISTANCE_M,
        )
    except (KeyError, TypeError, ValueError):
        print("  -> [失敗] 目前座標無法換算倒車目標。")
        return None

    mission_id = get_mission_guid_by_name(MOVE_TO_TARGET_MISSION_NAME)
    if not mission_id:
        return None

    position_name = f"reset_shelf_exit_{int(time.time())}"
    created = requests.post(
        f"{API_URL}/positions",
        json={
            "name": position_name,
            "map_id": map_id,
            "pos_x": exit_x,
            "pos_y": exit_y,
            "orientation": exit_orientation,
            "type_id": 0,
        },
        headers=HEADERS,
        timeout=REQUEST_TIMEOUT,
    )
    if created.status_code not in (200, 201):
        print(f"  -> [失敗] 建立倒車目標失敗：{created.status_code} {created.text}")
        return None
    try:
        position_guid = created.json().get("guid")
    except ValueError:
        position_guid = None
    if not position_guid:
        print("  -> [失敗] 倒車目標沒有 guid。")
        return None

    queued = requests.post(
        f"{API_URL}/mission_queue",
        json={
            "mission_id": mission_id,
            "parameters": [{"id": "target", "value": position_guid}],
        },
        headers=HEADERS,
        timeout=REQUEST_TIMEOUT,
    )
    if queued.status_code != 201:
        print(f"  -> [失敗] 派送倒車移動失敗：{queued.status_code} {queued.text}")
        delete_exit_position(position_guid)
        return None
    print(
        f"  -> 已派送倒車至暫時點 {position_name} "
        f"({exit_x:.2f}, {exit_y:.2f})。"
    )
    return position_guid


def delete_exit_position(position_guid):
    if not position_guid:
        return
    try:
        response = requests.delete(
            f"{API_URL}/positions/{position_guid}",
            headers=HEADERS,
            timeout=REQUEST_TIMEOUT,
        )
    except requests.RequestException as exc:
        print(f"  -> 刪除暫時倒車點失敗：{exc}")
        return
    if response.status_code not in (200, 204):
        print(f"  -> 刪除暫時倒車點失敗：{response.status_code} {response.text}")


def _linear_velocity(status):
    velocity = status.get("velocity") if isinstance(status, dict) else None
    if not isinstance(velocity, dict):
        return None
    try:
        return float(velocity.get("linear"))
    except (TypeError, ValueError):
        return None


def wait_until_left_shelf(start_xy):
    deadline = time.monotonic() + SHELF_EXIT_TIMEOUT_SECONDS
    while time.monotonic() < deadline:
        status = get_mir_status()
        if status_is_protective_stop(status):
            print("  -> [失敗] 倒車離開貨架時出現保護性停止或錯誤。")
            return False
        position = status.get("position") if isinstance(status, dict) else None
        try:
            distance = math.hypot(
                float(position["x"]) - start_xy[0],
                float(position["y"]) - start_xy[1],
            )
        except (TypeError, ValueError, KeyError):
            distance = 0.0
        speed = _linear_velocity(status)
        if distance >= SHELF_EXIT_CLEAR_M and speed is not None and abs(speed) < 0.05:
            print(f"  -> 已離開貨架，位移 {distance:.2f} 公尺。")
            return True
        time.sleep(LIFT_POLL_SECONDS)
    print("  -> [失敗] 倒車離開貨架逾時。")
    return False


def back_out_from_shelf():
    """頂升柱降到底之後，倒車離開貨架。離開前不派回充。"""
    print("[步驟 6] 倒車離開貨架...")
    status = get_mir_status()
    position = status.get("position") if isinstance(status, dict) else None
    try:
        start_xy = (float(position["x"]), float(position["y"]))
    except (TypeError, ValueError, KeyError):
        print("  -> [失敗] 無法讀取倒車前座標。")
        return False

    exit_position_guid = None
    try:
        relative_mission_id = find_relative_move_mission_id()
        if relative_mission_id and post_relative_shelf_exit(relative_mission_id):
            return wait_until_left_shelf(start_xy)
        print("  -> 找不到可用的相對移動任務，改派送到車後暫時點。")
        exit_position_guid = post_backoff_position_move(status)
        if not exit_position_guid:
            return False
        return wait_until_left_shelf(start_xy)
    finally:
        delete_exit_position(exit_position_guid)


def load_cart_transport_footprint_example():
    """讀載運任務裡的 Set footprint，沿用它的 action_type 與參數寫法。"""
    mission_id = get_mission_guid_by_name(CART_TRANSPORT_MISSION_NAME)
    if not mission_id:
        return None, None
    try:
        detail = requests.get(
            f"{API_URL}/missions/{mission_id}",
            headers=HEADERS,
            timeout=REQUEST_TIMEOUT,
        )
        actions = requests.get(
            f"{API_URL}/missions/{mission_id}/actions",
            headers=HEADERS,
            timeout=REQUEST_TIMEOUT,
        )
    except requests.RequestException as exc:
        print(f"  -> 讀取載運任務失敗，改用 set_footprint：{exc}")
        return None, None
    group_id = None
    if detail.status_code == 200:
        try:
            group_id = detail.json().get("group_id")
        except ValueError:
            group_id = None
    example = None
    if actions.status_code == 200:
        try:
            example = choose_set_footprint_action(actions.json())
        except ValueError:
            example = None
    if isinstance(example, dict):
        print(f"  -> 沿用載運任務的外形動作：{example.get('action_type')}")
    else:
        print("  -> 載運任務裡沒有 Set footprint 動作，改用 set_footprint。")
    return group_id, example if isinstance(example, dict) else None


def lookup_mission_group_id(preferred_group_id):
    if preferred_group_id:
        return preferred_group_id
    try:
        response = requests.get(
            f"{API_URL}/mission_groups",
            headers=HEADERS,
            timeout=REQUEST_TIMEOUT,
        )
    except requests.RequestException as exc:
        print(f"  -> [失敗] 讀取任務群組失敗：{exc}")
        return None
    if response.status_code != 200:
        print(f"  -> [失敗] 讀取任務群組失敗：{response.status_code} {response.text}")
        return None
    try:
        groups = response.json()
    except ValueError as exc:
        print(f"  -> [失敗] 任務群組無法解析：{exc}")
        return None
    if isinstance(groups, list):
        for group in groups:
            if isinstance(group, dict) and group.get("guid"):
                return group.get("guid")
    print("  -> [失敗] 沒有可用的任務群組，無法建立 Set footprint 任務。")
    return None


def ensure_robot_can_run_mission():
    """切換外形前，車子要能執行任務。保護性停止時不強制改狀態。"""
    status = get_mir_status()
    if status_is_protective_stop(status):
        print("  -> [失敗] 車子處於保護性停止或錯誤，無法執行切換外形任務。")
        return False
    if status.get("state_id") in (STATE_ID_READY, STATE_ID_EXECUTING):
        return True
    response = requests.put(
        f"{API_URL}/status",
        json={"state_id": STATE_ID_READY},
        headers=HEADERS,
        timeout=REQUEST_TIMEOUT,
    )
    if response.status_code != 200:
        print(
            "  -> [失敗] 無法切到 Ready 來執行切換外形任務："
            f"{response.status_code} {response.text}"
        )
        return False
    print("  -> 已切到 Ready，準備執行切換外形任務。")
    return True


def create_set_footprint_mission(
    footprint_name, footprint_value, group_id, action_type, parameter_id
):
    suffix = "wide" if footprint_name == WIDE_FOOTPRINT_NAME else "narrow"
    created = requests.post(
        f"{API_URL}/missions",
        json={
            "name": f"reset_set_footprint_{suffix}_{int(time.time() * 1000)}",
            "group_id": group_id,
            "hidden": True,
            "description": f"Reset Set footprint: {footprint_name}",
        },
        headers=HEADERS,
        timeout=REQUEST_TIMEOUT,
    )
    if created.status_code not in (200, 201):
        print(f"  -> [失敗] 建立切換外形任務失敗：{created.status_code} {created.text}")
        return None
    try:
        mission_guid = created.json().get("guid")
    except ValueError:
        mission_guid = None
    if not mission_guid:
        print("  -> [失敗] 切換外形任務沒有 guid。")
        return None
    action = build_set_footprint_action(
        action_type, parameter_id, footprint_value, mission_guid
    )
    posted = requests.post(
        f"{API_URL}/missions/{mission_guid}/actions",
        json=action,
        headers=HEADERS,
        timeout=REQUEST_TIMEOUT,
    )
    if posted.status_code not in (200, 201):
        print(f"  -> [失敗] 加入 Set footprint 動作失敗：{posted.status_code} {posted.text}")
        delete_temporary_mission(mission_guid)
        return None
    return mission_guid


def delete_temporary_mission(mission_guid):
    if not mission_guid:
        return
    try:
        response = requests.delete(
            f"{API_URL}/missions/{mission_guid}",
            headers=HEADERS,
            timeout=REQUEST_TIMEOUT,
        )
    except requests.RequestException as exc:
        print(f"  -> 刪除暫時外形任務失敗：{exc}")
        return
    if response.status_code not in (200, 204):
        print(f"  -> 刪除暫時外形任務失敗：{response.status_code} {response.text}")


def wait_for_footprint_mission(queue_id, target_points, footprint_name):
    """等到任務做完，而且 status 外形與目標多邊形相同。"""
    deadline = time.monotonic() + FOOTPRINT_SWITCH_TIMEOUT_SECONDS
    while time.monotonic() < deadline:
        try:
            status = get_mir_status()
        except requests.RequestException as exc:
            print(f"  -> 讀取外形狀態失敗：{exc}")
            time.sleep(LIFT_POLL_SECONDS)
            continue
        if status_is_protective_stop(status):
            print(f"  -> [失敗] 套用 {footprint_name} 時出現保護性停止。")
            return False
        matched = footprints_match(status.get("footprint"), target_points)
        state = ""
        if queue_id is not None:
            try:
                entry = get_mission_queue_entry(queue_id, None)
                state = str((entry or {}).get("state") or "")
            except requests.RequestException as exc:
                print(f"  -> 讀取外形任務狀態失敗：{exc}")
        if state.lower() in ("aborted", "abort", "error", "failed"):
            print(f"  -> [失敗] 外形任務結束狀態為 {state}。")
            return False
        if matched and state in ("", "Done"):
            print(f"  -> 已套用 {footprint_name}。")
            return True
        time.sleep(LIFT_POLL_SECONDS)
    try:
        status = get_mir_status()
    except requests.RequestException as exc:
        print(f"  -> 讀取外形狀態失敗：{exc}")
        status = {}
    if footprints_match(status.get("footprint"), target_points):
        print(f"  -> 已套用 {footprint_name}。")
        return True
    print(
        f"  -> [失敗] {FOOTPRINT_SWITCH_TIMEOUT_SECONDS} 秒內外形沒有變成 "
        f"{footprint_name}。"
    )
    return False


def apply_named_footprint(footprint_name):
    """派一筆只有 Set footprint 的任務來切換目前外形。已經是該外形則直接成功。"""
    listed = requests.get(
        f"{API_URL}/footprints", headers=HEADERS, timeout=REQUEST_TIMEOUT
    )
    if listed.status_code != 200:
        print(f"  -> [失敗] 讀取 Footprint 清單失敗：{listed.status_code} {listed.text}")
        return False
    try:
        footprints = listed.json()
    except ValueError as exc:
        print(f"  -> [失敗] Footprint 清單無法解析：{exc}")
        return False

    selected = choose_footprint_by_name(footprints, footprint_name)
    if not isinstance(selected, dict) or not selected.get("guid"):
        print(f"  -> [失敗] Footprint 清單沒有名稱為 {footprint_name} 的外形。")
        return False

    detail = requests.get(
        f"{API_URL}/footprints/{selected['guid']}",
        headers=HEADERS,
        timeout=REQUEST_TIMEOUT,
    )
    if detail.status_code != 200:
        print(
            f"  -> [失敗] 讀取 Footprint 失敗："
            f"{detail.status_code} {detail.text}"
        )
        return False
    try:
        footprint_detail = detail.json()
    except ValueError as exc:
        print(f"  -> [失敗] Footprint 內容無法解析：{exc}")
        return False
    if not isinstance(footprint_detail, dict):
        print("  -> [失敗] Footprint 內容不是物件。")
        return False
    footprint_detail.setdefault("guid", selected.get("guid"))
    footprint_detail.setdefault("url", selected.get("url"))
    target_points = footprint_detail.get("footprint_points")
    if target_points is None:
        target_points = footprint_detail.get("footprint")

    status = get_mir_status()
    if footprints_match(status.get("footprint"), target_points):
        print(f"  -> 目前已經是 {footprint_name}。")
        return True
    if not ensure_robot_can_run_mission():
        return False

    group_id, example = load_cart_transport_footprint_example()
    group_id = lookup_mission_group_id(group_id)
    if not group_id:
        return False
    action_type = SET_FOOTPRINT_ACTION_TYPE
    parameter_id = SET_FOOTPRINT_PARAMETER_ID
    if isinstance(example, dict) and example.get("action_type"):
        action_type = example.get("action_type")
        parameter_id = footprint_parameter_id(example)
    footprint_value = footprint_action_value(example, footprint_detail)
    mission_guid = create_set_footprint_mission(
        footprint_name, footprint_value, group_id, action_type, parameter_id
    )
    if not mission_guid:
        return False

    queue_id = None
    succeeded = False
    try:
        queued = requests.post(
            f"{API_URL}/mission_queue",
            json={"mission_id": mission_guid},
            headers=HEADERS,
            timeout=REQUEST_TIMEOUT,
        )
        if queued.status_code != 201:
            print(f"  -> [失敗] 派送切換外形任務失敗：{queued.status_code} {queued.text}")
            return False
        try:
            queue_id = queued.json().get("id")
        except ValueError:
            queue_id = None
        print(f"  -> 已派送 Set footprint 任務 ({footprint_name})，queue_id={queue_id}")
        succeeded = wait_for_footprint_mission(queue_id, target_points, footprint_name)
        return succeeded
    finally:
        if not succeeded:
            delete_mission_queue()
        delete_temporary_mission(mission_guid)


def apply_wide_footprint():
    """貨架還頂在車上時，先用任務套上寬外形，再降下頂升柱。"""
    print(f"[步驟 3] 以 Set footprint 任務套用寬外形 ({WIDE_FOOTPRINT_NAME})...")
    return apply_named_footprint(WIDE_FOOTPRINT_NAME)


def apply_narrow_footprint():
    """頂升柱降到底、貨架坐回架腳後，用任務改回空車窄外形。"""
    print(f"[步驟 5] 以 Set footprint 任務改回窄外形 ({NARROW_FOOTPRINT_NAME})...")
    return apply_named_footprint(NARROW_FOOTPRINT_NAME)


def dispatch_charge_mission():
    """Reset 成功後派送回充任務。找不到任務或 POST 失敗時切回 Pause。"""
    print(f"[步驟 7] 派送回充電樁任務 ({CHARGE_MISSION_NAME})...")
    charge_mission_id = get_mission_guid_by_name(CHARGE_MISSION_NAME)
    if not charge_mission_id:
        print(f"  -> [失敗] 找不到名稱為 '{CHARGE_MISSION_NAME}' 的 Mission。")
        pause_robot("找不到回充任務，停止 Reset")
        return False

    try:
        post_mission = requests.post(
            f"{API_URL}/mission_queue",
            json={"mission_id": charge_mission_id},
            headers=HEADERS,
            timeout=REQUEST_TIMEOUT,
        )
    except requests.RequestException as exc:
        print(f"  -> [失敗] 派送回充任務請求失敗：{exc}")
        pause_robot("派送回充任務請求失敗")
        return False

    if post_mission.status_code != 201:
        print(
            f"  -> [失敗] 派送回充任務失敗："
            f"{post_mission.status_code} {post_mission.text}"
        )
        pause_robot("派送回充任務失敗")
        return False

    print(f"  -> 已派送回充任務，mission_id={charge_mission_id}")
    return True


def read_lift_io_payload():
    """讀頂升柱 I/O。先讀即時 status，讀不到再讀模組本體。"""
    for path in (
        f"{API_URL}/io_modules/{TOP_LIFT_IO_GUID}/status",
        f"{API_URL}/io_modules/{TOP_LIFT_IO_GUID}",
    ):
        try:
            response = requests.get(path, headers=HEADERS, timeout=REQUEST_TIMEOUT)
        except requests.RequestException as exc:
            print(f"  -> 讀取頂升柱 I/O 失敗：{exc}")
            continue
        if response.status_code != 200:
            continue
        try:
            payload = response.json()
        except ValueError:
            continue
        if isinstance(payload, dict):
            return payload
    print("  -> [失敗] 讀不到頂升柱 I/O。")
    return None


def shelf_lift_is_up(payload):
    """Output 3 表示上升命令還開著。讀不到 output 時才看上升到位的 input 3。"""
    output_on = lift_output_is_on(payload, TOP_LIFT_UP_PORT)
    if output_on is not None:
        return output_on
    return lift_input_is_on(payload, TOP_LIFT_UP_INPUT)


def post_mission_queue(mission_id, parameters=None):
    payload = {"mission_id": mission_id}
    if parameters:
        payload["parameters"] = parameters
    response = requests.post(
        f"{API_URL}/mission_queue",
        json=payload,
        headers=HEADERS,
        timeout=REQUEST_TIMEOUT,
    )
    if response.status_code != 201:
        print(f"  -> [失敗] 派送任務失敗：{response.status_code} {response.text}")
        return None
    try:
        return response.json().get("id")
    except ValueError:
        return None


def wait_for_queued_mission(queue_id, mission_label, wait_through_estop=False):
    """等到這筆任務 Done。

    wait_through_estop=True 時：急停不立刻失敗，任務可留在 Pending，
    解除後繼續等 Done（與 Dashboard 行為一致）。
    """
    deadline = time.monotonic() + SHELF_UNLOAD_TIMEOUT_SECONDS
    announced_estop = False
    last_clear_at = 0.0
    while time.monotonic() < deadline:
        try:
            status = get_mir_status()
        except requests.RequestException as exc:
            print(f"  -> 讀取任務狀態失敗：{exc}")
            time.sleep(LIFT_POLL_SECONDS)
            continue

        if status_is_protective_stop(status):
            if not wait_through_estop:
                print(
                    f"  -> [失敗] {mission_label} 執行中出現急停、保護性停止或錯誤。"
                )
                return False
            if not announced_estop:
                print(
                    f"  -> {mission_label} 已在佇列；目前急停/錯誤，"
                    "等待解除後繼續執行（期間會重送 clear_error）..."
                )
                announced_estop = True
            now = time.monotonic()
            if now - last_clear_at >= 2.0:
                clear_robot_error()
                last_clear_at = now
        elif announced_estop:
            print(f"  -> 急停/錯誤已解除，繼續等待 {mission_label} 完成。")
            announced_estop = False

        state = ""
        if queue_id is not None:
            try:
                entry = get_mission_queue_entry(queue_id, None)
                state = str((entry or {}).get("state") or "")
            except requests.RequestException as exc:
                print(f"  -> 讀取任務佇列狀態失敗：{exc}")
        if state.lower() in ("aborted", "abort", "error", "failed"):
            print(f"  -> [失敗] {mission_label} 結束狀態為 {state}。")
            return False
        if state == "Done":
            print(f"  -> {mission_label} 已完成。")
            return True
        time.sleep(LIFT_POLL_SECONDS)
    print(
        f"  -> [失敗] {SHELF_UNLOAD_TIMEOUT_SECONDS} 秒內 "
        f"{mission_label} 沒有完成。"
    )
    return False


def run_named_mission(
    mission_name, announce_success=True, queue_while_stopped=False
):
    """派送具名任務並等待完成。

    queue_while_stopped=True：急停時仍 POST 進佇列（Pending），
    再等解除後執行到 Done。
    """
    mission_id = get_mission_guid_by_name(mission_name)
    if not mission_id:
        pause_robot("找不到重置任務，停止 Reset")
        return False

    if queue_while_stopped:
        try:
            status = get_mir_status()
        except requests.RequestException as exc:
            print(f"  -> 讀取狀態失敗，仍嘗試派送任務：{exc}")
            status = {}
        if status_is_protective_stop(status):
            print(
                "  -> 目前急停或錯誤，仍先派送任務進佇列（Pending），"
                "解除後會自動執行。"
            )
        elif not ensure_robot_can_run_mission():
            pause_robot("車子無法執行重置任務，停止 Reset")
            return False
    elif not ensure_robot_can_run_mission():
        pause_robot("車子無法執行重置任務，停止 Reset")
        return False

    queue_id = post_mission_queue(mission_id)
    if queue_id is None and queue_id != 0:
        pause_robot("派送重置任務失敗，停止 Reset")
        return False
    print(f"  -> 已派送 {mission_name}，queue_id={queue_id}")
    if not wait_for_queued_mission(
        queue_id, mission_name, wait_through_estop=queue_while_stopped
    ):
        pause_robot("重置任務未完成，停止 Reset")
        return False
    if announce_success:
        print("=== [成功] AMR 已完成 Reset ===")
    return True


def find_position_guid_by_name(position_name):
    response = requests.get(
        f"{API_URL}/positions", headers=HEADERS, timeout=REQUEST_TIMEOUT
    )
    if response.status_code != 200:
        print(f"  -> [失敗] 讀取位置清單失敗：{response.status_code} {response.text}")
        return None
    try:
        positions = response.json()
    except ValueError as exc:
        print(f"  -> [失敗] 位置清單無法解析：{exc}")
        return None
    if not isinstance(positions, list):
        print("  -> [失敗] 位置清單不是陣列。")
        return None
    for position in positions:
        if isinstance(position, dict) and position.get("name") == position_name:
            print(f"[找到] 位置名稱: {position_name} -> GUID: {position.get('guid')}")
            return position.get("guid")
    print(f"[失敗] 找不到名稱為 '{position_name}' 的位置")
    return None


def find_charge_position_name():
    """同「立即返回充電」：用 functions 取第一筆同名充電樁。"""
    import functions

    for name in CHARGE_POSITION_NAME_CANDIDATES:
        try:
            guid = functions.get_mission_point_uuid(name)
            print(f"[找到] 充電樁位置: {name} -> GUID: {guid}")
            return name
        except Exception:
            continue

    try:
        names = functions.get_mission_point_uuid_cmb() or []
    except Exception as exc:
        print(f"  -> [失敗] 讀取位置清單失敗：{exc}")
        names = []

    for name in names:
        if not name or "Charge" not in name:
            continue
        try:
            guid = functions.get_mission_point_uuid(name)
            print(f"[找到] 充電樁位置: {name} -> GUID: {guid}")
            return name
        except Exception:
            continue

    print("[失敗] 找不到充電樁位置（名稱需含 Charge）。")
    return None


def run_company_charge_move():
    """同「立即返回充電」：呼叫 functions.run_combo_location。"""
    import functions

    position_name = find_charge_position_name()
    if not position_name:
        pause_robot("無法派送回充電樁，停止 Reset")
        return False
    if not ensure_robot_can_run_mission():
        pause_robot("車子無法執行回充移動，停止 Reset")
        return False

    before_max_id = functions.get_mission_queue_max_id()
    functions.run_combo_location(position_name)
    print(f"✅ 已送出任務到充電站代碼: {position_name}")

    queue_id = None
    for _ in range(10):
        time.sleep(0.3)
        after_max_id = functions.get_mission_queue_max_id()
        if after_max_id is None:
            continue
        if before_max_id is None or after_max_id > before_max_id:
            queue_id = after_max_id
            break

    if queue_id is None:
        pause_robot("派送回充電樁失敗，停止 Reset")
        return False
    print(f"  -> 已派送回充電樁 {position_name}，queue_id={queue_id}")
    if not wait_for_queued_mission(queue_id, position_name):
        pause_robot("回充電樁未完成，停止 Reset")
        return False
    print("=== [成功] AMR 已完成 Reset，並已派送回充電樁 ===")
    return True


def reset_mir_complete():
    """清空佇列、降下頂升柱後派送 James_Reset_All（任務內含回充電樁）。"""
    print("=== 開始執行 MiR AMR Reset 完整流程 ===")

    try:
        print("[步驟 1] 清除錯誤 (clear_error)，不變更 MiR Status 為 Pause...")
        if not clear_robot_error():
            pause_robot("clear_error 失敗，停止 Reset")
            return False
        print("  -> 已送出 clear_error。")
        time.sleep(0.5)

        print("[步驟 2] 清空任務佇列，避免原本的任務繼續開往目的地...")
        if not delete_mission_queue():
            pause_robot("任務佇列清除失敗，停止 Reset")
            return False
        print("  -> 任務佇列已清空。")
        time.sleep(0.5)

        print(
            "[步驟 3] 以 I/O module REST 降下頂升柱 "
            f"(port {TOP_LIFT_UP_PORT} off → port {TOP_LIFT_DOWN_PORT} on)..."
        )
        if not command_lift_down():
            pause_robot("降下頂升柱失敗，停止 Reset")
            return False
        print("  -> 已送出降下頂升柱指令。")
        time.sleep(0.5)

        print(
            "[步驟 4] 派送重置任務 "
            f"({COMPANY_PLACE_AND_CHARGE_MISSION_NAME})..."
        )
        return run_named_mission(
            COMPANY_PLACE_AND_CHARGE_MISSION_NAME,
            announce_success=True,
            queue_while_stopped=True,
        )

    except requests.Timeout as e:
        print(f"\n[逾時] MiR API 超過 {REQUEST_TIMEOUT} 秒未回應：{e}")
        pause_robot("Reset 流程 API 逾時")
        return False
    except requests.RequestException as e:
        print(f"\n[連線錯誤] MiR API 請求失敗：{e}")
        pause_robot("Reset 流程 API 連線失敗")
        return False
    except Exception as e:
        print(f"\n[異常] 執行 Reset 過程中發生錯誤: {e}")
        pause_robot("Reset 流程發生未預期異常")
        return False


if __name__ == "__main__":
    print("請選擇功能：")
    print("1. 執行完整 Reset")
    print("2. 持續監控狀態並在異常時顯示建議措施")
    print("3. 監看所有 AMR 任務，結束時顯示並保存時間與距離")
    try:
        choice = input("輸入 1、2 或 3：").strip()
        if choice == "1":
            if not reset_mir_complete():
                sys.exit(1)
        elif choice == "2":
            monitor_mir()
        elif choice == "3":
            monitor_all_missions()
        else:
            print("選項無效，請重新執行並輸入 1、2 或 3。")
            sys.exit(2)
    except KeyboardInterrupt:
        print("\n已停止。")
