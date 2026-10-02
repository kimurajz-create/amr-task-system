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
TASK_METRICS_FILE = Path(__file__).with_name("mir_task_metrics.csv")

# 依 MiR API 文件：PUT /status 可設 Ready=3、Pause=4、Manual control=11；
# GET /status 的執行中、急停、錯誤狀態分別為 5、10、12。
STATE_ID_READY = 3
STATE_ID_PAUSE = 4
STATE_ID_EXECUTING = 5
STATE_ID_EMERGENCY_STOP = 10
STATE_ID_ERROR = 12

# 車頂頂升柱：與主程式 set_lift_position(False) 相同，internal IO 先關上升再開下降。
TOP_LIFT_IO_GUID = "mirconst-guid-0000-0001-internalIO00"
TOP_LIFT_DOWN_PORT = 2
TOP_LIFT_UP_PORT = 3
CHARGE_MISSION_NAME = "Charge"


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

def lower_top_lift():
    """強制降下車頂頂升柱。任一步失敗回傳 False，由呼叫端切回 Pause。"""
    url = f"{API_URL}/io_modules/{TOP_LIFT_IO_GUID}/status"
    sequence = [
        {"port": TOP_LIFT_UP_PORT, "on": False},
        {"port": TOP_LIFT_DOWN_PORT, "on": True},
    ]
    for cmd in sequence:
        payload = {**cmd, "timeout": 0}
        try:
            response = requests.put(
                url, json=payload, headers=HEADERS, timeout=REQUEST_TIMEOUT
            )
        except requests.RequestException as exc:
            print(f"  -> [失敗] Top Lift port {cmd['port']} 請求失敗：{exc}")
            return False
        if response.status_code != 200:
            print(
                f"  -> [失敗] Top Lift port {cmd['port']} 設定失敗："
                f"{response.status_code} {response.text}"
            )
            return False
        print(f"  -> Top Lift port {cmd['port']} 設為 {cmd['on']}")
        time.sleep(0.2)
    return True


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


def reset_mir_complete():
    """【一鍵 Reset】執行完整的 MiR Reset 流程"""
    print("=== 開始執行 MiR AMR Reset 完整流程 ===")

    try:
        # -------------------------------------------------------------------
        # 步驟 1: 清除錯誤。待執行清單的 stop/play 由主畫面按鈕處理，
        # 這裡不把 MiR Status 設成 Pause，否則無法執行後續降柱與回充。
        # -------------------------------------------------------------------
        print("[步驟 1] 清除錯誤 (clear_error)，不變更 MiR Status 為 Pause...")
        clear_res = requests.put(
            f"{API_URL}/status",
            json={"clear_error": True},
            headers=HEADERS,
            timeout=REQUEST_TIMEOUT,
        )
        if clear_res.status_code != 200:
            print(
                f"  -> [失敗] clear_error 失敗："
                f"{clear_res.status_code} {clear_res.text}"
            )
            pause_robot("clear_error 失敗，停止 Reset")
            return False
        print("  -> 已送出 clear_error。")
        time.sleep(0.5)

        # -------------------------------------------------------------------
        # 步驟 2: 清空內部所有任務佇列 (Delete Mission Queue) DELETE /mission_queue（不帶任何 ID）
        # 若是清除某一個任務佇列 DELETE /mission_queue/{id}（帶有具體 ID）
        # -------------------------------------------------------------------
        print("[步驟 2] 清空內部執行中與等待中的任務佇列...")
        del_res = requests.delete(
            f"{API_URL}/mission_queue", headers=HEADERS, timeout=REQUEST_TIMEOUT
        )
        if del_res.status_code == 204:
            print("  -> 任務佇列已順利清空。")
        else:
            print(
                f"  -> [失敗] 清除任務佇列未成功 (Status: {del_res.status_code}): {del_res.text}"
            )
            pause_robot("任務佇列清除失敗，停止 Reset")
            return False

        # -------------------------------------------------------------------
        # 步驟 3: Shelf Carrier 沒有 hook_status。直接降下頂升柱：
        # 先關上升腳位 3，再開下降腳位 2。
        # -------------------------------------------------------------------
        print("[步驟 3] 降下 Shelf Carrier 頂升柱（先關腳位 3，再開腳位 2）...")
        if not lower_top_lift():
            pause_robot("Top Lift 降下失敗，停止 Reset")
            return False
        print("  -> Top Lift 已送出降下指令。")

        # -------------------------------------------------------------------
        # 步驟 4: 重置 Footprint 為 default
        # -------------------------------------------------------------------
        print("[步驟 4] 重置 Footprint 為預設值 (default)...")
        fp_res = requests.put(
            f"{API_URL}/status",
            json={"footprint_code": "default"},
            headers=HEADERS,
            timeout=REQUEST_TIMEOUT,
        )
        if fp_res.status_code != 200:
            print(f"  -> [失敗] Footprint 還原失敗：{fp_res.status_code} {fp_res.text}")
            pause_robot("Footprint 還原失敗，停止 Reset")
            return False
        print("  -> Footprint 已還原為 default。")

        # -------------------------------------------------------------------
        # 步驟 5: 確認 GetStatus 有提供有效的位置座標
        # -------------------------------------------------------------------
        print("[步驟 5] 檢查地圖座標 (GetStatus position)...")
        status = get_mir_status()
        pos = status.get("position", {})
        try:
            coordinates = [float(pos[key]) for key in ("x", "y", "orientation")]
            coordinates_valid = all(math.isfinite(value) for value in coordinates)
        except (KeyError, TypeError, ValueError):
            coordinates_valid = False

        if not isinstance(pos, dict) or not coordinates_valid:
            print("  -> [失敗] GetStatus 未提供有效的 x/y/orientation，停止 Reset。")
            pause_robot("座標無效，停止 Reset")
            return False

        print(
            f"  -> 當前座標: X={coordinates[0]:.2f}, Y={coordinates[1]:.2f}, Orientation={coordinates[2]:.2f}"
        )
        print("  -> API 欄位未提供定位信心度，此處只確認座標有效，不代表信心度已驗證。")

        # -------------------------------------------------------------------
        # 步驟 6: 切換至 Ready 狀態等待新命令
        # -------------------------------------------------------------------
        print(f"[步驟 6] 將狀態切換至 Ready (State ID: {STATE_ID_READY})...")
        ready_res = requests.put(
            f"{API_URL}/status", json={"state_id": STATE_ID_READY}, headers=HEADERS,
            timeout=REQUEST_TIMEOUT,
        )

        if ready_res.status_code != 200:
            print(
                f"  -> [失敗] 切換至 Ready 狀態失敗: "
                f"{ready_res.status_code} {ready_res.text}"
            )
            pause_robot("切換 Ready 失敗，停止 Reset")
            return False

        # Ready + default Footprint 後，等待安全 PLC 結束特殊模式；只讀回報欄位，
        # 不直接 PUT safety_system_muted。欄位缺失或仍為 True 都不視為成功。
        print("  -> 等待安全系統退出 Muted 狀態並確認 enabled...")
        safety_deadline = time.monotonic() + 10
        last_safety_status = None
        while time.monotonic() < safety_deadline:
            try:
                last_safety_status = get_mir_status().get("safety_system_muted")
                if last_safety_status is False:
                    print("  -> 已確認 safety_system_muted=False (enabled)。")
                    if not dispatch_charge_mission():
                        return False
                    print("=== [成功] AMR 已完成 Reset，空車 Ready，並已派送回充任務 ===")
                    return True
            except requests.RequestException as exc:
                last_safety_status = f"讀取失敗：{exc}"
            time.sleep(1)

        print(f"  -> [失敗] 未能確認安全系統已 enabled；最後讀取值：{last_safety_status!r}。")
        pause_robot("安全系統仍為 Muted 或狀態無法確認")
        print("  -> 請確認現場狀況及 MiR 安全系統，確認恢復後再重新執行 Reset。")
        return False

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
