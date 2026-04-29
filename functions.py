import requests
from requests.auth import HTTPBasicAuth
import time
import base64
import hashlib
from PySide6.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout,QMessageBox
from datetime import datetime
import pytz
import json
import os

CONFIG_PATH = "config.json"
MIR_IP = ""  # 請替換成你的 MiR AMR IP http://10.11.202.251
Full_IP = ""
API_USER = "Distributor"
API_PASSWORD = "distributor"  # 請替換成你的 API 密碼
DEFAULT_CONFIG = {
    "MIR_IP": "http://10.11.202.251",
    "heartbeat_display_count": 13,
}
##################################IP############################################
# 從設定檔讀取 IP，並且回傳這個 IP
def load_config():
    config = {}

    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                loaded = json.load(f)
                if isinstance(loaded, dict):
                    config = loaded
        except Exception:
            config = {}

    merged_config = DEFAULT_CONFIG.copy()
    merged_config.update(config)
    return merged_config


def save_config(config):
    merged_config = DEFAULT_CONFIG.copy()
    if isinstance(config, dict):
        merged_config.update(config)

    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(merged_config, f, ensure_ascii=False, indent=2)


def load_ip():
    config = load_config()
    return config.get("MIR_IP", DEFAULT_CONFIG["MIR_IP"])


def load_heartbeat_display_count():
    config = load_config()

    try:
        count = int(config.get("heartbeat_display_count", DEFAULT_CONFIG["heartbeat_display_count"]))
    except (TypeError, ValueError):
        count = DEFAULT_CONFIG["heartbeat_display_count"]

    return max(0, min(13, count))
    
def save_ip(ip):
    config = load_config()
    config["MIR_IP"] = ip
    save_config(config)

#auth_encoded = 'RGlzdHJpYnV0b3I6NjJmMmYwZjFlZmYxMGQzMTUyYzk1ZjZmMDU5NjU3NmU0ODJiYjhlNDQ4MDY0MzNmNGNmOTI5NzkyODM0YjAxNA=='
#HEADERS = {"Content-Type": "application/json","Accept": "application/json"}


##################################Status############################################

# 🔹 產生 API 認證 Header
def get_auth_headers():
    password_sha256 = hashlib.sha256(API_PASSWORD.encode()).hexdigest()  # SHA-256 加密密碼
    auth_str = f"{API_USER}:{password_sha256}"  # 格式化字串
    auth_encoded = base64.b64encode(auth_str.encode()).decode()  # Base64 編碼
    return {
        "Authorization": f"Basic {auth_encoded}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

# 確認MiR API 連線確認狀態 raw 版本且沒用到
def check_api_status():
    url = f"{MIR_IP}/api/v2.0.0/status"
    headers = get_auth_headers()
    response = requests.get(url,headers=headers)
    if response.status_code == 200:
        print(f"API 回應成功: {response.status_code},{response.text}")
    else:
        print(f"API 錯誤: {response.status_code}, {response.text}")

# 確認MiR API 連線確認狀態 
def check_api_status_v2():
    try:
        url = f"{Full_IP}/api/v2.0.0/status"
        headers = get_auth_headers()
        response = requests.get(url,headers=headers)
        if response.status_code == 200:
            return 0
        else:
            print(f"API 錯誤: {response.status_code}, {response.text}")
            return 1
    except Exception as e:
        # print("⚠️ 發生連線錯誤：", e)
        return 1


# 確認MiR API 連線確認狀態 
def check_api_status_v3():
    try:
        url = f"{MIR_IP}/api/v2.0.0/status"
        headers = get_auth_headers()

        response = requests.get(url, headers=headers, timeout=3)

        if response.status_code != 200:
            raise Exception(f"API error: {response.status_code}")
        return response.json()
    except Exception as e:
        print("❌ API exception:", e)
        raise e   # ⭐ 一定要丟出去





# 取得MiR所有資料
def check_MiR_status():
    url = f"{MIR_IP}/api/v2.0.0/status"
    headers = get_auth_headers()
    response = requests.get(url,headers=headers)
    if response.status_code == 200:
        #print(f"API 回應成功")
        return response.json()
    else:
        print(f"API 錯誤: {response.status_code}, {response.text}")

# 取得MiR state_id
def get_mission_text():
    status = check_api_status_v3()
    return status.get("mission_text")

def check_MiR_status_state_ID():
    url = f"{MIR_IP}/api/v2.0.0/status"
    headers = get_auth_headers()
    response = requests.get(url, headers = headers)
    if response.status_code ==200:
        nums = response.json()
        return nums["state_id"]
    else:
        print(f"API 錯誤: {response.status_code}, {response.text}")

# 取得MiR map_id
def check_MiR_status_maps_ID():
    url = f"{MIR_IP}/api/v2.0.0/status"
    headers = get_auth_headers()
    response = requests.get(url, headers = headers)
    if response.status_code ==200:
        strings = response.json()
        return strings["map_id"]
    else:
        print(f"API 錯誤: {response.status_code}, {response.text}")

# 取得MiR battery % 
def get_battery_level():
    url = f"{MIR_IP}/api/v2.0.0/status"
    headers = get_auth_headers()
    response = requests.get(url, headers = headers)
    if response.status_code ==200:
        percentage = response.json()
        return percentage["battery_percentage"]
    else:
        print(f"API 錯誤: {response.status_code}, {response.text}")


# 取得MiR Position
def check_MiR_status_position():
    url = f"{MIR_IP}/api/v2.0.0/status"
    headers = get_auth_headers()
    response = requests.get(url, headers = headers)
    if response.status_code ==200:
        data = response.json()
        positions = data["position"]
        return positions["x"],positions["y"]
    else:
        print(f"API 錯誤: {response.status_code}, {response.text}")

# MiR error清除改成Ready
def clear_MiR_error():
    url = f"{MIR_IP}/api/v2.0.0/status"
    headers = get_auth_headers()
    status_data_clear = {"clear_error": True}
    response = requests.put(url,json = status_data_clear,headers = headers)
    if response.status_code == 200:
        print("成功清除錯誤")
    else:
        print("重製失敗")
    status_data_state_id = {"state_id":3}
    response = requests.put(url,json = status_data_state_id,headers = headers)
    if response.status_code == 200:
        print("成功改變任務狀態 pause->ready")
    else:
        print("重製失敗")

##################################Maps############################################
# 取得當前地圖的position
def get_curmaps_positions_cmb():
    map_guid = check_MiR_status_maps_ID()
    url = f"{MIR_IP}/api/v2.0.0/maps/{map_guid}/positions"
    headers = get_auth_headers()
    # 送出 API 請求
    response = requests.get(url,headers = headers)
    if response.status_code == 200:
        positions = response.json()
        names = [position["name"] for position in positions]
        # print(names)
        return names
    else:
        print(f"API 錯誤: {response.status_code}, {response.text}")
        

##################################Positions############################################
# 取得地圖上的任務點(標誌)的guid 
def get_mission_point_uuid(point_name):
    url = f"{MIR_IP}/api/v2.0.0/positions"
    headers = get_auth_headers()
    # 送出 API 請求
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        positions = response.json()
        for position in positions:
            if position["name"] == point_name:
                return position["guid"]
    raise Exception(f"找不到地圖任務點: {point_name}")



# 取得所有地圖位置的點的名字，放入cmb
def get_mission_point_uuid_cmb():
    url =f"{MIR_IP}/api/v2.0.0/positions"
    headers = get_auth_headers()
    # 送出 API 請求
    response = requests.get(url,headers=headers)
    if response.status_code == 200:
        positions = response.json()
        names = [position["name"] for position in positions]
        return names
    
# 新增 "Sent robot to" Marker
def post_position(x,y,z):
    url =f"{MIR_IP}/api/v2.0.0/positions"
    headers = get_auth_headers()
    map_id = check_MiR_status_maps_ID()
    data = {
        "name": "Sent robot to",
        "pos_x": x,
        "pos_y": y,
        "orientation": z,
        "type_id":0,
        "map_id":map_id
    }
    response = requests.post(url,json = data,headers = headers)
    if response.status_code == 201:
        print(f"post position success")
    else:
        print(f"post position fail")

# 刪除剛建好的position
def delete_srt_position():
    srt_guid = get_mission_point_uuid("Sent robot to")
    url =f"{MIR_IP}/api/v2.0.0/positions/{srt_guid}"
    headers = get_auth_headers()
    response = requests.delete(url,headers=headers)
    if response.status_code == 204:
        print(f"Sent robot to delete success")
    else:
        print(f"Sent robot to delete fail")


##################################Missions############################################


# 取得任務 guid
def get_mission_id(mission_name): 
    url = f"{MIR_IP}/api/v2.0.0/missions"
    headers = get_auth_headers()
    response = requests.get(url,headers = headers)
    if response.status_code == 200:
        missions = response.json()
        for mission in missions:
            if mission["name"] == mission_name:
                return mission["guid"]
    else:
        print(f"❌ 無法取得任務列表: {response.text}")


# 取得任務列表所有任務名字，用於放入cmb
def get_mission_id_cmb():
    url = f"{MIR_IP}/api/v2.0.0/missions"
    headers = get_auth_headers()
    response = requests.get(url,headers = headers)
    if response.status_code == 200:
        missions = response.json()
        names = [mission["name"] for mission in missions]
        return names
    else:
        print(f"❌ 無法取得任務列表: {response.text}")

# 取得任務群組所有任務名字，用於放入cmb
def get_mission_groups_id_cmb():
    url = f"{MIR_IP}/api/v2.0.0/mission_groups/mirconst-guid-0000-0011-missiongroup/missions"
    headers = get_auth_headers()
    response = requests.get(url,headers = headers)
    if response.status_code == 200:
        missions = response.json()
        names = [mission["name"] for mission in missions]
        return names
    else:
        print(f"❌ 無法取得任務列表: {response.text}")


##################################Mission_queue############################################

# 取得當下mission_queue的"id"
def get_mission_queue_max_id():
    url = f"{MIR_IP}/api/v2.0.0/mission_queue"
    headers = get_auth_headers()
    response = requests.get(url,headers = headers)
    if response.status_code == 200:
        mission_queue_list = response.json() 
        return max(item["id"] for item in mission_queue_list if "id" in item)
    else:
        print(f"❌ 無法取得mission_queue列表_01: {response.text}")

# 取得當下mission_queue的"id"的state
def get_mission_queue_max_id_state():
    max_id = get_mission_queue_max_id()
    url = f"{MIR_IP}/api/v2.0.0/mission_queue/{max_id}"
    headers = get_auth_headers()
    response = requests.get(url,headers = headers)
    if response.status_code == 200:
        mission_data = response.json() 
        return mission_data['state']
    else:
        print(f"❌ 無法取得mission_queue列表_02: {response.text}")
    
# 取得已知mission_queue的"id"的state
def get_mission_queue_id_state(mission_queue_id):
    url = f"{MIR_IP}/api/v2.0.0/mission_queue/{mission_queue_id}"
    headers = get_auth_headers()
    response = requests.get(url,headers = headers)
    if response.status_code == 200:
        mission_data = response.json() 
        return mission_data['state']
    else:
        print(f"❌ 無法取得mission_queue列表_03: {response.text}")



# 發送移動命令(透過任務id、地圖id當參數，搭配dashboard那邊的Mission設定移動任務才行)
def move_to_position(mission_id,position_uuid):
    url = f"{MIR_IP}/api/v2.0.0/mission_queue"
    mission_data = {
        "mission_id": mission_id,
        "parameters": [{"id": "target", "value": position_uuid}]
    }
    print(mission_data) 
    headers = get_auth_headers()
    response = requests.post(url, json=mission_data, headers=headers)
    if response.status_code == 201:
        print(f"成功發送移動至 {position_uuid} 的指令")
    else:
        print(f"移動失敗: {response.text}")


# 多變數版，發送移動命令(透過任務id、地圖id當參數，搭配dashboard那邊的Mission設定移動任務才行)
def move_to_position_multi_var(start_uuid,goal_uuid,mission_id):
    url = f"{MIR_IP}/api/v2.0.0/mission_queue"
    mission_data = {
        "mission_id": mission_id,
        "parameters": [{"id": "target", "value": start_uuid},{"id": "target_2", "value": goal_uuid}]
    }
    print(f"任務參數:{mission_data}") 
    headers = get_auth_headers()
    response = requests.post(url, json=mission_data, headers=headers)
    if response.status_code == 201:
        print(f"成功發送移動至 {goal_uuid} 的指令")
        mission_queue_max_id = get_mission_queue_max_id()
        print(f"MiR Dashboard mission_queue_max_id 編號:{mission_queue_max_id}")
    else:
        print(f"移動失敗: {response.text}")




# 執行任務
def start_the_mission(ref_mission_id):
    url = f"{MIR_IP}/api/v2.0.0/mission_queue"
    mission_data = {
        "mission_id": ref_mission_id
    }
    headers = get_auth_headers()
    response = requests.post(url, json=mission_data, headers=headers)
    if response.status_code == 201:
        print(f"成功發送任務指令")
    else:
        print(f"移動失敗: {response.text}")

# 執行相對移動任務
def run_relative_move(rela_mission_id,x_m,y_m,ori):
    url = f"{MIR_IP}/api/v2.0.0/mission_queue"
    mission_data = {
        "mission_id":rela_mission_id,
        "parameters":[{"id":"x","value":x_m},{"id":"y","value":y_m},{"id":"ori","value":ori}]
    }
    headers = get_auth_headers()
    response = requests.post(url, json = mission_data,headers = headers)
    if response.status_code == 201:
        print(f"成功發送相對移動任務")
    else:
        print(f"發送移動任務失敗: {response.text}")

# 中斷所有等待與執行中任務
def stop_the_mission():
    url = f"{MIR_IP}/api/v2.0.0/mission_queue"
    headers = get_auth_headers()
    response = requests.delete(url,headers = headers)
    if response.status_code == 204:
        print(f"成功執行中斷任務")
    else:
        print(f"中斷失敗: {response.text}")


# 發送語音或提示音 X 
def play_sound(sound_type):
    url = f"{MIR_IP}/api/v2.0.0/sounds"
    sound_data = {"type": sound_type}  # 例如 "beep" 或 "speech"
    # 更新 Header，加上 Authorization
    headers = get_auth_headers()
    response = requests.post(url, json=sound_data, headers=headers)
    if response.status_code == 201:
        print(f"成功播放提示音: {sound_type}")
    else:
        print(f"播放失敗: {response.text}")


# 取得等待中任務名字
def get_pending_mission_names():
    url = f"{MIR_IP}/api/v2.0.0/mission_queue"
    headers = get_auth_headers()
    response = requests.get(url,headers = headers)
    if response.status_code == 200:
        states = response.json()
        # pending_ids = [state["id"] for state in states if state["state"] == "Pending"]
        # return pending_ids
        pending_names = []
        for state in states:
            if state["state"] == "Pending":
                pending_ids = state["id"]
                url = f"{MIR_IP}/api/v2.0.0/mission_queue/{pending_ids}"
                response = requests.get(url,headers = headers)
                if response.status_code == 200:
                    states_02 = response.json()
                    url_mission_id =states_02["mission"]
                    #print(url_mission_id)
                    url = f"{MIR_IP}/api{url_mission_id}" # 網址找名字
                    #print(url)
                    response = requests.get(url,headers = headers)
                    if response.status_code == 200:
                        mission_data = response.json()
                        mission_name = mission_data["name"]
                        pending_names.append(mission_name)
                    else:
                        print(f"❌ 無法取得當前等待任務id_03: {response.text}")
                else:
                    print(f"❌ 無法取得當前等待任務id_02: {response.text}")
        #print(pending_names)
        return pending_names
    else:
        print(f"❌ 無法取得當前等待任務id: {response.text}")

##################################IO_Modules############################################

# module設定開關功能
def set_lift_position(up: bool):
    url = f"{MIR_IP}/api/v2.0.0/io_modules/mirconst-guid-0000-0001-internalIO00/status"
    headers = get_auth_headers()

    # 腳位定義
    DOWN_PORT = 2
    UP_PORT = 3

    if up:
        # 先關下降 → 再開上升
        sequence = [
            {"port": DOWN_PORT, "on": False},
            {"port": UP_PORT, "on": True}
        ]
    else:
        # 先關上升 → 再開下降
        sequence = [
            {"port": UP_PORT, "on": False},
            {"port": DOWN_PORT, "on": True}
        ]

    for cmd in sequence:
        payload = {**cmd, "timeout": 0}
        response = requests.put(url, json=payload, headers=headers)
        if response.status_code == 200:
            print(f"Port {cmd['port']} 設為 {cmd['on']}")
        else:
            print(f"Port {cmd['port']} 設定失敗：{response.text}")

        time.sleep(0.2)


######################################功能型Function###################################################

''' POST /mission_queue RESTFUL API 正確下法
{
  "mission_id": "f94d241b-0083-11f0-8c63-000e8eb5c919",
  "parameters": 
  [
    {"id": "target", "value": "14d381d5-0539-11f0-a30e-000e8eb5c919"}
  ]
}

{
  "mission_id": "bd397531-9e91-11f0-a0ff-000e8eb5c919",
  "parameters": [
    {"id": "target", "value": "14d381d5-0539-11f0-a30e-000e8eb5c919"},{"id": "target_2", "value": "a6c5a5bc-02de-11f0-bb2d-000e8eb5c919"},{"id": "target_3", "value": "095327a3-02df-11f0-bb2d-000e8eb5c919"}
  ]
}
'''

# 執行任務(地圖)地圖名字要注意!!!!Critical
def run_combo_location(map_marker):
    # 如果字串包含marker or Charge
    if("marker" in map_marker or "Charge" in map_marker):
        point_uuid = get_mission_point_uuid(map_marker)
        mission_id = get_mission_id("DockToTarget_Critical")
        move_to_position(mission_id,point_uuid)
    else:
        point_uuid = get_mission_point_uuid(map_marker)
        mission_id = get_mission_id("MoveToTarget_Critical")
        move_to_position(mission_id,point_uuid)


# 執行任務(地圖)地圖名字要注意!!!!Critical
def run_combo_location_multi_var(start,goal,mission):
        point_uuid_start = get_mission_point_uuid(start)
        point_uuid_goal = get_mission_point_uuid(goal)       
        mission_id = get_mission_id(f"{mission}")
        print(f"起點uuid:{point_uuid_start},終點uuid:{point_uuid_goal},任務id:{mission_id}")
        move_to_position_multi_var(point_uuid_start,point_uuid_goal,mission_id)
        
   
    

####################################取得error歷史資料#####################################################

# 取得錯誤時任務的id數字 
def get_error_status_msqid():
    url = f"{MIR_IP}/api/v2.0.0/status"
    headers = get_auth_headers()
    response = requests.get(url, headers = headers)
    if response.status_code == 200:
        states = response.json()
        if states["state_text"] == "Error":
            #return states["mission_queue_id"] #這邊會是null
            return 0
        else:
            #print("當前state不是Error")
            return 1
    else:
        print(f"❌ 無法取得當前任務狀態: {response.text}")
        return 1

# 取得最大ID的Mission
def get_latest_id():
    url = f"{MIR_IP}/api/v2.0.0/mission_queue"
    headers = get_auth_headers()
    response = requests.get(url,headers = headers)
    if response.status_code == 200:
        data = response.json()
        valid_states = ["Aborted","Done"]
        # 從 data 中，把 state 有出現在 valid_states 裡的資料挑出來，組成一個新的 list，叫做 filtered
        # 要放進去的東西 for 每一筆資料 in 原始資料 if 條件成立
        filtered = [x for x in data if x["state"] in valid_states]
        if filtered:
            # 傳入 x，回傳 x["id"]，匿名函式
            latest_mission = max(filtered, key=lambda x:x["id"])
            # print(f"最新的 mission ID: {latest_mission['id']}")
            # print(f"狀態: {latest_mission['state']}")
            # print(f"完整資訊: {latest_mission}")
            return latest_mission['id']
        else:
            print("沒有符合條件的任務")
    else:
        print("API 回傳為空")
        return 1

# 取得mission_id、開始、結束時間 
def get_mission_info(msq_id):
    url = f"{MIR_IP}/api/v2.0.0/mission_queue/{msq_id}"
    #print(url)
    headers = get_auth_headers()
    response = requests.get(url, headers = headers)
    if response.status_code == 200:
        data = response.json()
        return data["mission_id"],data["id"],data["message"],data["started"],data["finished"],
    else:
        print(f"❌ 無法取得任務開始結束時間: {response.text}")
        return 1

# 取得任務的名字
def get_mission_name(ms_id):
    url = f"{MIR_IP}/api/v2.0.0/missions/{ms_id}"
    #print(url)
    headers = get_auth_headers()
    response = requests.get(url,headers = headers)
    if response.status_code == 200:
        data = response.json()
        return data["name"]
    else:
        return 1
    
# 時間轉換
def convert_to_tw(iso_str):
    dt = datetime.fromisoformat(iso_str)
    tz_tw = pytz.timezone("Asia/Taipei")
    return dt.astimezone(tz_tw).strftime("%Y-%m-%d %H:%M:%S")

def get_error_history_data():
    error_flag = get_error_status_msqid()
    #print(error_flag)
    if error_flag == 0:
        id = get_latest_id()
        #print(id)     
        mission_info = get_mission_info(id)
        #print(mission_info)
        start_str = convert_to_tw(mission_info[3])
        finish_str = convert_to_tw(mission_info[4])
        name = get_mission_name(mission_info[0])
        #print(f"name：{name}","id:",mission_info[1],"description:",mission_info[2],"Start:",start_str,"Finish:",finish_str)
        
        result = {
            "name":name,
            "id":mission_info[1],
            "description": mission_info[2],
            "Start": start_str,
            "Finish": finish_str
        }
        return result
    else:
        #print("no error")
        return None








  




    
