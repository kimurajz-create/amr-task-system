import sys
import os
import json
import ipaddress
import numpy as np
import requests
import random
import time
import functions
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QTableWidget, QWidget,
    QPushButton, QVBoxLayout, QMessageBox, QCompleter,
    QLabel, QScrollArea, QFrame, QTableWidgetItem,QHeaderView,QHBoxLayout,QSizePolicy,QListWidgetItem
)
from PySide6.QtGui import (
    QPixmap, QPainter, QPen, QIcon, QPalette,
    QColor, QMouseEvent,QBrush
)
from PySide6.QtCore import (
    QTimer, QDateTime, Qt,QSize
)
# 引入我們寫好的資料庫管理器
from TaskDBManager import TaskDBManager
from ui_main import Ui_MainWindow

# ----------------------------------------------------------------------
# 1. 數據層：定義 MiR 英文代碼與中文名稱的對應關係
# 這是你的「翻譯字典」英翻中，工程語言轉user語言
# ----------------------------------------------------------------------
USER_LOCATION_MAP = {
    "LbV2_Robot position Hua": "華陀會議室",
    "LbV2_Robot position lecture hall 02": "演講廳_02",
    "LbV2_Robot position lecture hall 01": "演講廳_01",
    "LbV2_Robot position Sofa3": "沙發3",
    "LbV2_Robot position Sofa2": "沙發2",
    "LbV2_Robot position Sofa1": "沙發1",
    "LbV2_Robot position Reception V2": "櫃台",
    "LbV2_MiR Charge 48V V2": "充電樁",
    "LbV2_Robot position Elv  Bridge Map": "電梯橋",
}

USER_MISSION_GROUP_MAP ={
    "0813_narrow_road": "窄路測試",
    "ACE_Elv_0625": "電梯",
    "Lobby Demo Reception to lecture hall 01": "Demo_櫃台到演講廳_01並返回櫃台",
    "Lobby Demo Reception to lecture hall 02": "Demo_櫃台到演講廳_02並返回櫃台",
    "Lobby Demo Reception to Sofa1": "Demo_櫃台到沙發1並返回櫃台",
    "Lobby Demo Reception to Sofa2": "Demo_櫃台到沙發2並返回櫃台",
    "Lobby Demo Reception to Sofa3": "Demo_櫃台到沙發3並返回櫃台",
    "Lobby Demo Seminar Presentation Jordan": "Demo_櫃台出發大廳繞一圈",
    "WNC_Test01":"WNC",
    "Lobby Demo Cart Transport": "Demo_載貨運輸",
    "Lobby Demo Empty Cart Transport": "Demo_空車運輸",
}

REQUIRED_MISSION_CODES = {
    "Lobby Demo Cart Transport",    # 載貨運輸
    "Lobby Demo Empty Cart Transport", # 空車運輸
}

# 反轉字典：方便載入 ComboBox 時，以中文為 Key，中翻英
MIR_LOCATION_MAP = {v: k for k, v in USER_LOCATION_MAP.items()}
MIR_MISSION_GROUP_MAP = {v: k for k, v in USER_MISSION_GROUP_MAP.items()}

CHARGING_STATION_NAME = "充電樁"

# ----------------------------------------------------------------------
# 2. 界面層：定義通知項目的視覺外觀
class NotificationItem(QWidget):
    """
    客製化單一通知項目的視覺外觀
    """
    def __init__(self, type, message, parent=None):
        super().__init__(parent)

        # 根據類型定義樣式
        if type == "完成":
            bg_color = "#D4EDDA"  # 淺綠色
            icon_text = "✅ 成功"
        elif type == "警告":
            bg_color = "#FFF3CD"  # 黃色
            icon_text = "⚠️ 警告"
        else: # 錯誤或一般
            bg_color = "#F8D7DA"  # 紅色系
            icon_text = "❌ 錯誤"
        
        # 如果你希望所有東西都緊密貼合，請按照以下順序檢查並設置：
        # QListWidget CSS：確保 QListWidget::item 的 margin 和 padding 為 0px。
        # NotificationItem CSS：確保 NotificationItem 的 margin 為 0px 0。
        # NotificationItem Layout：確保 main_layout.setContentsMargins(0, 0, 0, 0)。

        # 設置 Widget 的背景顏色和圓角
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {bg_color};
                border-radius: 5px;
                color: #000000;
                margin: 0px 0; /* 在項目上下留點空間 */
            }}
        """)
        
        # 設定主佈局 (水平排列：圖標 - 訊息 - 伸縮空間 - 按鈕)
        main_layout = QHBoxLayout(self)
        # 將 layout 的上下左右內邊界都設為 0
        main_layout.setContentsMargins(0, 0, 0, 0) #10,8,10,8 = 上,下,左,右
        main_layout.setSpacing(10)

        # 1. 圖標標籤
        icon_label = QLabel(icon_text)
        icon_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        main_layout.addWidget(icon_label)

        # 2. 訊息內容 (自動換行)
        message_label = QLabel(message)
        message_label.setWordWrap(True)
        message_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        main_layout.addWidget(message_label)

        # # 1. 訊息內容 (圖標、類型和詳細訊息合併在同一個 QLabel 內)
        # full_message = f'<span style="font-weight: bold;">{icon_text}</span> {message}'
        # message_label = QLabel(full_message)
        # message_label.setWordWrap(True)
        # message_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        
        # 這裡使用富文本 (Rich Text) 來讓 "✅ 成功：" 部分粗體，而訊息保持常規
        message_label.setTextFormat(Qt.RichText)
        main_layout.addWidget(message_label)

        # # 3. 讓訊息內容自動伸展
        # main_layout.addStretch() 

        # 4. 關閉按鈕 (X)
        close_btn = QPushButton("X")
        close_btn.setFixedSize(20, 20)
        close_btn.setStyleSheet("QPushButton { border: none; font-size: 18px; color: #555; background-color: transparent; }")
        main_layout.addWidget(close_btn)
        
        # 將關閉按鈕存為屬性，供外部連接訊號
        self.close_button = close_btn

class MainWindow(QMainWindow, Ui_MainWindow):
    # 主函式
    def __init__(self):
        super().__init__()
        self.setupUi(self) # 使用這行來設定 UI 元素
        ########################################QTableWidget右下待執行任務表格########################################
        #右邊待執行任務表格 
        self.tableWidget_pending_mission_list.setHorizontalHeaderLabels([" ","序", "流水號", "起點", "目的地", "任務", "狀態","操作"])
        # 隱藏左側的垂直表頭
        self.tableWidget_pending_mission_list.verticalHeader().setVisible(False)
        # 禁用右上角的角落區塊
        self.tableWidget_pending_mission_list.setCornerButtonEnabled(False)
        # 在表格中添加一行
        self.tableWidget_pending_mission_list.setItem(0, 1, QTableWidgetItem("1"))
        self.tableWidget_pending_mission_list.setItem(0, 2, QTableWidgetItem("7123"))
        self.tableWidget_pending_mission_list.setItem(0, 3, QTableWidgetItem("減菌室-1"))
        self.tableWidget_pending_mission_list.setItem(0, 4, QTableWidgetItem("手術室04-A"))
        self.tableWidget_pending_mission_list.setItem(0, 5, QTableWidgetItem("拉車至指定定點"))
        self.tableWidget_pending_mission_list.setItem(0, 6, QTableWidgetItem("執行中"))
        self.tableWidget_pending_mission_list.setItem(0, 7, QTableWidgetItem(" "))
        # 呼叫我們剛剛建立的函式來置中所有文字
        self.set_table_items_center(self.tableWidget_pending_mission_list)

        # 設定列寬度的自適應策略
        self.header = self.tableWidget_pending_mission_list.horizontalHeader()
        self.header.setSectionResizeMode(4, QHeaderView.Stretch)
        self.header.setSectionResizeMode(5, QHeaderView.Stretch)
        
        # 設置表格行高
        self.tableWidget_pending_mission_list.setWordWrap(True)
        self.tableWidget_pending_mission_list.resizeRowsToContents()

        # --- 1. 資料庫連線設定 (請根據你的遠端 IP 修改 'host') ---
        DB_CONFIG = {
            'user': 'postgres',
            'host': 'localhost',
            'database': 'military_mir250_project',
            'password': '123456',
            'port': 5432
        }
        self.db_manager = TaskDBManager(DB_CONFIG) # 將目標傳遞給工具
        self.db_manager.connect() # 叫工具開始連線

        #是否按下開始載運 cccccccc
        self.is_running=False
        #是否AMR idle等待 cccccc
        self.is_AMR_idle=True
        #是否低電輛需充電 cccccccc
        self.is_low_battery=False
        #是否已無任務 cccccccc
        self.is_no_mission=False

        self.is_online = True
        # 載入已儲存的IP，並在初始化時顯示此IP
        functions.MIR_IP = functions.load_ip()
        IP = functions.MIR_IP
        if IP.startswith("http://"):
            IP=IP[7:]
        self.lineEdit_IP.setText(IP)

        # 暫時隱藏frame 0923
        self.frame_temp.hide()

        if self.is_online:
            # ----------------------------------------
            # 1. 快速定時器 (Fast Polling) - 例如 300ms
            # 用於即時性要求高的資訊：位置、即時狀態
            # ----------------------------------------
            self.fast_timer = QTimer(self)
            # 連接需要快速更新的函式
            self.fast_timer.timeout.connect(self.query_mir_info)
            self.fast_timer.timeout.connect(self.poll_mir_position)
            # 啟動快速定時器
            self.fast_timer.start(0.3 * 1000) # 秒
            # ----------------------------------------
            # 2. 慢速定時器 (Slow Polling) - 例如 5 秒
            # 用於即時性要求低的資訊：電量、歷史資料
            # ----------------------------------------
            self.slow_timer = QTimer(self)
            # 連接需要慢速更新的函式
            self.slow_timer.timeout.connect(self.query_battery_status)
            self.slow_timer.timeout.connect(self.query_his_data)
            # 啟動慢速定時器
            self.slow_timer.start(10 * 1000) # 10 秒
            # ----------------------------------------
            # 3. 設置 QTimer 自動刷新清單 (核心功能) ---
            # ----------------------------------------
            self.refresh_timer = QTimer(self)
            # 定時觸發 refresh_task_list 函式
            self.refresh_timer.timeout.connect(self.refresh_task_list)
            self.refresh_timer.timeout.connect(self.query_mir_status_db)
            # 每 2000 毫秒 (2 秒) 刷新一次
            self.refresh_timer.start(2000) 
            
            # 第一次手動載入清單
            self.refresh_task_list()
            #cmb載入地圖Markers
            self.load_map_positions()
            #cmb載入任務名字
            # self.load_mission_positions()
            self.load_mission_groups_positions()

        # 讀圖
        self.original_pixmap = QPixmap("./picture/MiR floor plan_V5_Demo")
        if self.original_pixmap.isNull():
            print("圖片讀取失敗！")
        else:
            self.label_map_1.setPixmap(self.original_pixmap)
            self.label_map_1.resize(self.original_pixmap.size())
            # 印出原始圖片尺寸（寬 x 高）
            width = self.original_pixmap.width()
            height = self.original_pixmap.height()
            # print(f"原始圖片大小：{width} x {height}")
          
        # # 讀logo
        # self.icon_pixmap = QPixmap("./picture/aceicon1.png")
        # if self.icon_pixmap.isNull():
        #     print("圖片讀取失敗！")
        # else:
        #     self.label_logo.setPixmap(self.icon_pixmap)

        # Flag
        self.clicked_enabled = False

        # 三個對應點（像素座標）充電站，左下角牆角，櫃台上方
        self.image_pts = np.array([[200,130],[126,355],[563,274],],dtype = np.float32)
        # 三個對應點（MiR 世界座標）
        # 地圖"Lobby"座標 
        # self.world_pts = np.array([[-0.867, 27.335], [-7.411, 7.937],[31.021, 15.012],], dtype=np.float32)
        # 地圖"Lobby_V2"座標 
        self.world_pts = np.array([[1.465, 28.374], [-5.091, 9.006],[34.138, 17.249],], dtype=np.float32)
        # 建立仿射轉換矩陣
        self.affine_matrix = self.compute_affine_transform()
        # self.draw_car_position(-5.397, 7.455) 
        # self.poll_mir_position()

        #點擊按鈕觸發任務
        self.btn_StartMission.clicked.connect(self.on_map_location_clicked)
        self.btn_StartMission2.clicked.connect(self.on_start_mission_clicked)
        self.btn_StartRelativeMove.clicked.connect(self.on_relative_move_clicked)
        self.btn_UpdateInfo.clicked.connect(self.on_update_info_clicked)
        self.btn_ChargeMission.clicked.connect(self.on_start_chargestation_clicked)
        # self.btn_GetPM.clicked.connect(self.on_get_pending_mssion_clicked) 取得等待中任務 暫時停用
        self.btn_GetPM.hide() # 暫時隱藏
        self.btn_StopMission1.clicked.connect(self.on_stop_mission_clicked)
        self.btn_StopMission2.clicked.connect(self.on_stop_mission_clicked)
        self.btn_Reset.clicked.connect(self.on_reset_status_clicked)
        self.btn_save_ip.clicked.connect(self.on_save_ip_clicked)
        self.btn_IO_Up.clicked.connect(self.on_up_io_clicked)
        self.btn_IO_down.clicked.connect(self.on_down_io_clicked)
        self.btn_SentRobotTo.setEnabled(False)
        self.btn_SentRobotTo.clicked.connect(self.on_sent_robot_to_clicked)
        self.btn_Add_New_Mission.clicked.connect(self.on_add_new_mission_clicked)
        # self.setFixedSize(1440,768)
        self.setFixedSize(1920,1080)

        #勾選觸發任務
        self.chb_map.stateChanged.connect(self.toggle_click_mode_map)

        # 設置 QListWidget 的樣式表
        self.listWidget_msg.setStyleSheet("""
            QListWidget {
                /* 移除邊框和邊距 */
                border: none; 
                padding: 0px; 
                background-color: #ffffff; /* 如果表格背景是深色，這裡也設為深色或透明 */
            }
            QListWidget::item {
                margin: 1px; /* 移除項目之間的預設邊距 */
                padding: 0px; /* 移除項目本身的內邊距 */
            }
        """)

        # self.add_notification_item("完成", "7811 任務完成: 從 減菌室-9 前往 手術室01-A")
        # self.add_notification_item("警告", "電量低於 20%，任務暫停，請立即處理。")
        # self.add_notification_item("錯誤", "9999 任務失敗：目標點座標錯誤。")
    
    #######################UXUI_tablewidget#######################
   
    # 將 QTableWidget 中所有單元格的文字設定為置中
    def set_table_items_center(self, table_widget):
        for row in range(table_widget.rowCount()):
            for col in range(table_widget.columnCount()):
                item = table_widget.item(row, col)
                if item is not None:
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

    #  添加刪除按鈕
    #  self.add_delete_button(row_count)
        
    # 建立一個刪除按鈕
    # 建立一個刪除按鈕
    def add_delete_button(self, row):
        """建立一個帶有刪除圖示的按鈕，並加入表格"""

        # 建立一個中央對齊的 Widget (容器)
        container_widget = QWidget()
        layout = QHBoxLayout(container_widget)

        # 設置佈局的間距和邊界為 0，讓按鈕可以置中 (這是對的)
        layout.setContentsMargins(0, 0, 0, 0)
     
        # 建立一個 QPushButton
        delete_btn = QPushButton("")
        delete_btn.setFixedSize(30, 30) # 強制設定按鈕的固定大小
        
        # 載入垃圾桶圖示
        delete_icon = QIcon(":/icons/icons/trash-2.svg") 
        delete_btn.setIcon(delete_icon)
        delete_btn.setIconSize(QSize(20, 20)) 
        
        # 設置按鈕的樣式 (省略部分樣式程式碼)
        delete_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF5252;
                border: none;
                border-radius: 12px;
                padding: 2px;
            }
        """)
        
        # 將按鈕加入佈局 (現在按鈕在容器內置中了)
        layout.addWidget(delete_btn)
        
        # 連接按鈕的點擊事件到一個刪除函式
        delete_btn.clicked.connect(lambda: self.delete_row(row))
        
        # 將這個中央對齊的 Widget (包含按鈕) 放入表格單元格
        self.tableWidget_pending_mission_list.setCellWidget(row, 7, container_widget)
        
    # 刪除表格中的行
    def delete_row(self, row):
        """根據行號刪除表格中的行"""
        self.tableWidget_pending_mission_list.removeRow(row)

    # 新增一條通知到清單
    def add_notification_item(self, type, message):
        """
        將客製化的 NotificationItem 加入到 self.listWidget_msg 中
        """
        # 1. 創建客製化 Widget
        notification_widget = NotificationItem(type, message)
        
        # 2. 創建 QListWidgetItem 作為容器
        list_item = QListWidgetItem(self.listWidget_msg)
        
        # 3. 設定 QListWidgetItem 的高度以容納 widget
        list_item.setSizeHint(notification_widget.sizeHint())
        
        # 4. 將客製化 Widget 設定給 QListWidgetItem
        self.listWidget_msg.setItemWidget(list_item, notification_widget)
        
        # 5. 將新項目放到最上方 (實現最新的通知在最上面)
        self.listWidget_msg.insertItem(0, list_item)

        # 6. 連接關閉按鈕的事件：點擊時刪除該項目
        close_btn = notification_widget.close_button
        
        # 這是關鍵步驟：點擊按鈕時，取得 list_item 的行號並刪除
        close_btn.clicked.connect(
            lambda: self.listWidget_msg.takeItem(self.listWidget_msg.row(list_item))
        )

    def closeEvent(self, event):
        """
        程式關閉時，安全關閉資料庫連線。
        """
        if self.db_manager:
            self.db_manager.close()
        super().closeEvent(event)

    #######################postgresql資料庫#######################
    # 在DB新增任務
    def on_add_new_mission_clicked(self):

        start_place = self.cmb_location2.currentText()
        destination = self.cmb_location.currentText()
        mission_content = self.cmb_mission.currentText()
        
        # 檢查欄位是否為空
        if not start_place or not destination or not  mission_content :
            print("請填寫所有欄位！")
            return
        
        # 呼叫 TaskDBManager 寫入 DB
        # DB 會自動處理 sequence (排隊順序) 和 id (流水號)
        new_id = self.db_manager.add_new_task(start_place, destination, mission_content)
        print("new_id", new_id)

        if new_id:
            print(f"✅ 新增任務成功，DB ID: {new_id}")
            self.cmb_location2.setCurrentIndex(0)
            self.cmb_location.setCurrentIndex(0)
            self.cmb_mission.setCurrentIndex(0)
        
            # 刷新表格，顯示新任務
            self.refresh_task_list()
        else:
            print("❌ 寫入資料庫失敗。") 

   
   # 讀DB然後刷新GUI表格
    def refresh_task_list(self):
        """
        [QTimer 連接的函式]
        從 DB 查詢 'Pending' 或 'Executing' 任務，並刷新 QTableWidget。
        """
        # 呼叫 TaskDBManager 取得待執行任務 (已依 sequence 排序)
        tasks = self.db_manager.get_pending_tasks()
    

        # 確保表格總欄數為 8 欄 (1個隱藏DB_ID + 7個顯示欄位)
        if self.tableWidget_pending_mission_list.columnCount() != 8:
            print(self.tableWidget_pending_mission_list.columnCount())
            # 如果你的初始化沒設定，在這裡設定一次
            self.tableWidget_pending_mission_list.setColumnCount(8)
            self.tableWidget_pending_mission_list.setColumnHidden(0, True)
        else:
            self.tableWidget_pending_mission_list.setColumnHidden(0, True)

        # 1. 清空表格設定行數為 0
        self.tableWidget_pending_mission_list.setRowCount(0)
        if not tasks:
            return
        
        self.tableWidget_pending_mission_list.setRowCount(len(tasks))

        # 2. 遍歷任務並填充表格
        for row_idx, task in enumerate(tasks):
            # 任務物件 (task) 是一個字典，Key 對應 DB 欄位名稱
            # A. 隱藏欄位 (索引 0)
            self.tableWidget_pending_mission_list.setItem(row_idx, 0, QTableWidgetItem(str(task['id']))) 
            
            # B. 顯示欄位 (索引 1 開始) - **注意索引偏移**
            
            # 索引 1: 序
            self.tableWidget_pending_mission_list.setItem(row_idx, 1, QTableWidgetItem(str(task['sequence'])))
            
            # 索引 2: 流水號 (使用 DB 的 mission_content 或其他欄位)
            # 註: 如果你的 DB 任務資訊中沒有獨立的「流水號」欄位，可能需要調整 DB 設計
            self.tableWidget_pending_mission_list.setItem(row_idx, 2, QTableWidgetItem(str(task['id']))) 
            
            # 索引 3: 起點
            self.tableWidget_pending_mission_list.setItem(row_idx, 3, QTableWidgetItem(task['start_point']))
            
            # 索引 4: 目的地
            self.tableWidget_pending_mission_list.setItem(row_idx, 4, QTableWidgetItem(task['target_point']))

            # 索引 5: 任務 (這裡對應你 UI 標題的「任務」，可能是 mission_content 的完整描述)
            self.tableWidget_pending_mission_list.setItem(row_idx, 5, QTableWidgetItem(task['mission_content']))
            
            # 索引 6: 狀態
            item_status = QTableWidgetItem(task['status'])
            
            # 根據狀態給予顏色提示 (可選)
            if task['status'] == 'Executing':
                item_status.setForeground(QColor('green'))
            elif task['status'] == 'Pending':
                item_status.setForeground(QColor('#FFA500'))
            self.tableWidget_pending_mission_list.setItem(row_idx, 6, item_status)
            
            # 索引 7: 空白/操作按鈕欄位
            # self.tableWidget_pending_mission_list.setItem(row_idx, 7, ) 
            self.add_delete_button(row_idx) # add_delete_button
            

            # 重新呼叫你的置中函式和列寬調整 (這不會被前面的 setRowCount(0) 影響)
            self.set_table_items_center(self.tableWidget_pending_mission_list)
            self.tableWidget_pending_mission_list.resizeRowsToContents()

    #######################自動詢問#################################

    # 自動詢問當前任務狀態與等待中任務
    def query_mir_info(self):
        try:
            status_info = functions.check_MiR_status()
            #轉換成「格式化的 JSON 字串」，用來方便顯示（indent=4 表示用四個空格縮排）
            status_info_str = json.dumps(status_info, indent = 4) 
            timestamp = QDateTime.currentDateTime().toString("yyyy-MM-dd HH:mm:ss")
            full_message = f"[{timestamp}] 狀態：\n{status_info_str}\n{'-'*40}"
            self.plntxtEdit_Info.appendPlainText(full_message)
            #取得等待任務名字
            pm_names = functions.get_pending_mission_names()
            if pm_names:
                pm_names_with_index = [f"任務{index+1} {name}" for index, name in enumerate(pm_names)]
                self.txtEdit_GetPM.setPlainText("\n".join(pm_names_with_index))
                #self.txtEdit_GetPM.setPlainText("\n".join(pm_names))
            else:
                self.txtEdit_GetPM.setPlainText("No pending missions")
                
            state_ID = functions.check_MiR_status_state_ID()
            if state_ID == 12:
                self.label_Status_1.setText("Status：Error") 
                self.label_Status_1.setStyleSheet("color: purple;font-size: 24px;")
            elif state_ID == 1:
                self.label_Status_1.setText("Status：Starting") 
                self.label_Status_1.setStyleSheet("color: yellow;font-size: 24px;")
            elif state_ID == 2:
                self.label_Status_1.setText("Status：ShuttingDown") 
                self.label_Status_1.setStyleSheet("color: red;font-size: 24px;")
            elif state_ID == 3:
                self.label_Status_1.setText("Status：Ready") 
                self.label_Status_1.setStyleSheet("color: green;font-size: 24px;")
            elif state_ID == 4:
                self.label_Status_1.setText("Status：Pause") 
                self.label_Status_1.setStyleSheet("color: yellow;font-size: 24px;")
            elif state_ID == 5:
                self.label_Status_1.setText("Status：Executing") 
                self.label_Status_1.setStyleSheet("color: green;font-size: 24px;")
            elif state_ID == 6:
                self.label_Status_1.setText("Status：Aborted")
                self.label_Status_1.setStyleSheet("color: yellow;font-size: 24px;")
            elif state_ID == 7:
                self.label_Status_1.setText("Status：GoalReached")
                self.label_Status_1.setStyleSheet("color: green;font-size: 24px;")
            elif state_ID == 8:
                self.label_Status_1.setText("Status：Docked")
                self.label_Status_1.setStyleSheet("color: green;font-size: 24px;")
            elif state_ID == 9:
                self.label_Status_1.setText("Status：Docking")
                self.label_Status_1.setStyleSheet("color: green;font-size: 24px;")
            elif state_ID == 10:
                self.label_Status_1.setText("Status：EmergencyStop")
                self.label_Status_1.setStyleSheet("color: red;font-size: 24px;")
            elif state_ID == 11:
                self.label_Status_1.setText("Status：ManualControl")
                self.label_Status_1.setStyleSheet("color: red;font-size: 24px;")
        except Exception as e:
            self.label_Status_1.setText("錯誤")

    # 詢問車子狀態
    def query_mir_status_db(self):
        executing_task_data = self.db_manager.get_currently_executing_task()
        # 檢查是否有正在執行的任務
        if not executing_task_data:
            # 沒有任務在執行，直接退出
            return
        
        task_id = executing_task_data['id']
        start_point = executing_task_data['start_point']
        target_point = executing_task_data['target_point']

        state_ID = functions.check_MiR_status_state_ID()

        if state_ID == 3:
            self.is_AMR_idle=True
            self.db_manager.update_task_status(task_id, new_status="Completed")
            print(f"✅ 任務 ID {task_id} 已由機器人完成，狀態更新為 Completed。")
            self.add_notification_item("完成", f"{task_id} 任務完成: 從 {start_point} 前往 {target_point}")

        # 刷新 UI 任務列表
        self.refresh_task_list() 
        
        # 接著自動執行下一個任務 (可選，如果你想自動連續跑)
        # self.on_map_location_clicked() 
            
        # [可選] 如果你需要處理錯誤狀態 (例如 state_ID == 12)
        # elif state_ID == 12: 
        #     self.db_manager.update_task_status(task_id, new_status="Error")
        #     print(f"❌ 任務 ID {task_id} 執行失敗，狀態更新為 Error。")

            

    # 自動詢問Sent robot to車子狀態
    def query_mir_status(self):
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.query_mir_status_ready)
        self.status_timer.start(5000)
        
    # 自動詢問到了沒
    def query_mir_status_ready(self):
        state_id = functions.check_MiR_status_state_ID()
        if state_id == 3:
            print("導航完成，刪除位置")
            self.status_timer.stop()
            functions.delete_srt_position()
        self.load_map_positions()


    # 自動詢問電池狀態
    def query_battery_status(self):
        battery_level = functions.get_battery_level()
        # 根據電量設定顏色
        if battery_level <=20:
            color = "red"
            self.add_notification_item("警告", f"電量低於 {battery_level}%，任務暫停，暫回充電樁充電。")
            self.is_low_battery=True  #低電量旗標設定 ccccc
        elif battery_level <=50 and battery_level>=20:
            color = "orange"
            self.is_low_battery=False  #低電量旗標設定 ccccc
        elif battery_level ==100:
            color = "#085508"
            self.add_notification_item("完成", f"電量已恢復到 {battery_level}%，接續執行。")
            self.is_low_battery=False  #低電量旗標設定 ccccc
        else:
            color = "#085508"
            self.is_low_battery=False  #低電量旗標設定 ccccc
        # 設定進度條顏色。沒有設定 ::chunk 樣式時，Qt 有時會不渲染 chunk 或讓它預設尺寸極小

        self.progressBar_battery.setStyleSheet(f"""
        QProgressBar {{
            color: black;  
            border: 2px solid grey; 
            border-radius: 5px;
            text-align: center;
            font-size: 16px;
        }}
        QProgressBar::chunk {{
            background-color: {color};
        }}
        """)
        self.progressBar_battery.setValue(battery_level)
        
    # 自動取得歷史錯誤資料
    def query_his_data(self):
        his_data = functions.get_error_history_data()
        if his_data:
            response = requests.post("http://localhost:3000/upload", json=his_data)
            print("伺服器回應：", response.json())
        else:
            # print("沒有錯誤，不需要送出資料") 0923
            pass

    ##################################按鈕############################################

    # 按鈕(取得等待任務名字) #暫時停用
    def on_get_pending_mssion_clicked(self):
        pm_names = functions.get_pending_mission_names()
        if pm_names:
            self.txtEdit_GetPM.setPlainText("\n".join(pm_names))
        else:
            self.txtEdit_GetPM.setPlainText("No pending missions")


    # 按鈕(取得當前任務狀態)
    def on_update_info_clicked(self):
        status_info = functions.check_MiR_status()
        #轉換成「格式化的 JSON 字串」，用來方便顯示（indent=4 表示用四個空格縮排）
        status_info_str = json.dumps(status_info, indent = 4) 
        self.plntxtEdit_Info.setPlainText(status_info_str)
        state_ID = functions.check_MiR_status_state_ID()
        if state_ID == 12:
            self.label_Status_1.setText("Status：Error") 
            self.label_Status_1.setStyleSheet("color: purple;font-size: 24px;")
        elif state_ID == 1:
            self.label_Status_1.setText("Status：Starting") 
            self.label_Status_1.setStyleSheet("color: yellow;font-size: 24px;")
        elif state_ID == 2:
            self.label_Status_1.setText("Status：ShuttingDown") 
            self.label_Status_1.setStyleSheet("color: red;font-size: 24px;")
        elif state_ID == 3:
            self.label_Status_1.setText("Status：Ready") 
            self.label_Status_1.setStyleSheet("color: green;font-size: 24px;")
        elif state_ID == 4:
            self.label_Status_1.setText("Status：Pause") 
            self.label_Status_1.setStyleSheet("color: yellow;font-size: 24px;")
        elif state_ID == 5:
            self.label_Status_1.setText("Status：Executing") 
            self.label_Status_1.setStyleSheet("color: green;font-size: 24px;")
        elif state_ID == 6:
            self.label_Status_1.setText("Status：Aborted")
            self.label_Status_1.setStyleSheet("color: yellow;font-size: 24px;")
        elif state_ID == 7:
            self.label_Status_1.setText("Status：GoalReached")
            self.label_Status_1.setStyleSheet("color: green;font-size: 24px;")
        elif state_ID == 8:
            self.label_Status_1.setText("Status：Docked")
            self.label_Status_1.setStyleSheet("color: green;font-size: 24px;")
        elif state_ID == 9:
            self.label_Status_1.setText("Status：Docking")
            self.label_Status_1.setStyleSheet("color: green;font-size: 24px;")
        elif state_ID == 10:
            self.label_Status_1.setText("Status：EmergencyStop")
            self.label_Status_1.setStyleSheet("color: red;font-size: 24px;")
        elif state_ID == 11:
            self.label_Status_1.setText("Status：ManualControl")
            self.label_Status_1.setStyleSheet("color: red;font-size: 24px;")
        
        
    # 按鈕(回去充電站)
    def on_start_chargestation_clicked(self):

        # 嘗試從字典中獲取充電站的英文代碼
        # 如果找不到 "充電樁" 這個 Key，就回傳 None
        charge_code = MIR_LOCATION_MAP.get(CHARGING_STATION_NAME)
        if charge_code:
            functions.run_combo_location(charge_code)
            print(f"✅ 已送出任務到充電站代碼: {charge_code}")
        else:
            QMessageBox.critical(self, "錯誤！", "🚨 請檢查 MiR 名稱是否被更改，或字典是否遺漏了 '充電樁' 的定義。")
            
            
            

    # 按鈕(重製任務狀態)
    def on_reset_status_clicked(self):
        functions.clear_MiR_error()

    # 按鈕(前往地圖位置) 
    def on_map_location_clicked(self):
        self.is_running=True
        while self.is_running:
            # 呼叫 TaskDBManager 取得最高優先權任務
            # priority_tasks = [{'id': 7, 'sequence': 7, 'start_point': '櫃台', 'target_point': '實驗室C', 'mission_content': '運送文件', 'status': 'Pending'}]
            priority_tasks = self.db_manager.get_highest_priority_task()
            if priority_tasks is None:
                self.is_no_mission=True
                while self.is_no_mission:
                    # 命令AMR去充電站(需coding) ccccccccc
                    time.sleep(0.1)
                    QApplication.processEvents()  # ✅ 強制刷新 UI   
                    if self.is_running==False:
                        # 命令AMR去充電站(需coding) ccccccccc
                        break
                    priority_tasks = self.db_manager.get_highest_priority_task()
                    if priority_tasks is not None:
                        self.is_no_mission=False
                        break
            
            mir_code_id = priority_tasks[0]['id']
            mir_code_s = priority_tasks[0]['start_point']
            mir_code_d = priority_tasks[0]['target_point']      
            mir_code = priority_tasks[0]['mission_content']

            mir_code_s = MIR_LOCATION_MAP.get(mir_code_s)
            mir_code_d = MIR_LOCATION_MAP.get(mir_code_d)
            mir_code = MIR_MISSION_GROUP_MAP.get(mir_code)

            # mir_code_s = self.cmb_location2.currentData()
            # mir_code_d = self.cmb_location.currentData()
            # mir_code = self.cmb_mission.currentData()
            charge_code = MIR_LOCATION_MAP.get(CHARGING_STATION_NAME)

            if "Charge" in mir_code_d:
                if mir_code and mir_code_s and mir_code_d:
                    # functions.run_combo_location(mir_code)
                    functions.run_combo_location_multi_var(mir_code_s,mir_code_d,mir_code)
                    self.db_manager.update_task_status(mir_code_id, new_status="Executing", command_sent=True)
                    functions.run_combo_location(charge_code)
                    print(f"✅ 已送出前往任務到 MiR 代碼: {mir_code}")
                else:
                    # 處理沒有選中任何選項的情況
                    print("❌ 地點或對應代碼無效。")
            else:
                if mir_code and mir_code_s and mir_code_d:
                    # functions.run_combo_location(mir_code)
                    print(mir_code_s,mir_code_d,mir_code)
                    functions.run_combo_location_multi_var(mir_code_s,mir_code_d,mir_code)
                    self.db_manager.update_task_status(mir_code_id, new_status="Executing", command_sent=True)
                    print(f"✅ 已送出前往任務到 MiR 代碼: {mir_code}")
                else:
                    # 處理沒有選中任何選項的情況
                    print("❌ 地點或對應代碼無效。")
            QApplication.processEvents()  # ✅ 強制刷新 UI

            # 等待前一任務完成 cccccccc
            print("等待任務完成....")
            while not self.is_AMR_idle:
                time.sleep(0.1)
                QApplication.processEvents()  # ✅ 強制刷新 UI   

            if self.is_running==False:
                # 命令AMR去充電站(需coding) ccccccccc
                break       

            if self.is_low_battery:
                time.sleep(0.1)
                # 命令AMR去充電站(需coding) ccccccccc  
                while self.is_low_battery:
                    time.sleep(0.1)
                    QApplication.processEvents()  # ✅ 強制刷新 UI       
        
    # 按鈕(中斷執行中與等待任務)
    def on_stop_mission_clicked(self):
        self.is_running=False
        functions.stop_the_mission()
    
     # 按鈕(執行特定任務) 
    def on_start_mission_clicked(self):
        # 取得任務ID(GUID)
        mission_guid = functions.get_mission_id(self.cmb_mission.currentText())
        functions.start_the_mission(mission_guid)

    # 按鈕(執行相對移動任務)
    def on_relative_move_clicked(self):
        x = self.dsb_x.value()
        y = self.dsb_y.value()
        ori = self.dsb_ori.value()
        mission_guid = functions.get_mission_id(self.cmb_mission.currentText())
        functions.run_relative_move(mission_guid,x,y,ori)

    # 按鈕(輸入ip)
    def on_save_ip_clicked(self):
        """
        處理儲存 IP 按鈕的點擊事件。
        負責：清理輸入、驗證 IP 格式、測試 API 連線，並在成功時儲存 IP 設定。
        """
        # 1. 取得與清理輸入
        # 去除輸入字串開頭與結尾的空白字元
        IP = self.lineEdit_IP.text().strip()
        try:
            # 2. 移除協議頭 (若存在)
            # 如果使用者輸入了完整的 "http://" 協議頭，將其移除，只保留 IP 或域名
            if IP.startswith("http://"):
                IP = IP[7:]
            # 3. IP 格式驗證
            # 嘗試將字串解析為有效的 IP 位址 (IPv4 或 IPv6)。
            # 如果格式錯誤，會拋出 ValueError。
            ipaddress.ip_address(IP)
            # 4. 建立全域 IP 變數 (純 IP 和完整 URL)
            functions.MIR_IP = IP                # 儲存純 IP/域名 到全域變數
            full_ip = f"http://{IP}"             # 建立帶有 http:// 的完整 URL
            functions.Full_IP = full_ip          # 儲存完整 URL 到全域變數
            # 5. 連線狀態測試
            # 呼叫外部函式，檢查此 IP 的 API 是否可連線 (例如 MiR 機器人)
            test_url = functions.check_api_status_v2()
            # 6. 處理測試結果
            if test_url == 0:
                # 連線成功
                functions.save_ip(full_ip)       # ✅ 寫入檔案，作為下次啟動的預設 IP
                functions.MIR_IP = full_ip       # ✅ 即時更新全域變數，使程式立即使用新 IP
                print("成功儲存 IP:", full_ip)
            elif test_url == 1:
                # 連線失敗
                self.show_error(f"無法連線到車子") # 顯示錯誤訊息給使用者
        except ValueError:
            # 格式錯誤處理
            # 如果 ipaddress.ip_address(IP) 失敗，表示格式無效
            print("無效的 IP 格式")
            # 這裡可以加上 self.show_error("無效的 IP 格式") 提醒使用者

    # 按鈕(IO_Module UP)
    def on_up_io_clicked(self):
        functions.set_lift_position(True)

    # 按鈕(IO_Module Down) 
    def on_down_io_clicked(self):
        functions.set_lift_position(False)

    # 按鈕(Sent robot to go)
    def on_sent_robot_to_clicked(self):
        X=self.dsb_x_m.value()
        Y=self.dsb_y_m.value()
        Z=self.dsb_ori_m.value()
        print(X,Y,Z)
        functions.post_position(X,Y,Z)
        self.load_map_positions()
        functions.run_combo_location("Sent robot to")
        self.query_mir_status()

    ##################################勾選框############################################
    
    # 地圖點擊啟用勾選
    def toggle_click_mode_map(self,state):
        print("state =", state)
        self.clicked_enabled = (state == 2)
        if state == 2:
            self.btn_SentRobotTo.setEnabled(True)
        else:
            self.btn_SentRobotTo.setEnabled(False)
        print(self.clicked_enabled)
        print("點擊模式已", "啟用" if self.clicked_enabled else "關閉")


    ##################################下拉式選單############################################

   

    # 取得地圖名字
    def load_map_positions(self):
        self.cmb_location.clear()
        self.cmb_location2.clear()

        # 獲取 MiR 系統回傳的所有英文代碼列表
        mir_codes_list = functions.get_curmaps_positions_cmb() 

        user_names_list = []
        # print("--- 字典 Key 對應診斷 ---")
        # print("MiR 傳回的代碼列表:", mir_codes_list)

        if mir_codes_list:
            for mir_code in mir_codes_list:

                # 查找中文名稱，如果找不到，就顯示原始的英文代碼
                # 字典名稱.get(Key,Default Value)。A (第一個參數)，Python 會嘗試將這個值作為 Key 去字典裡查找。B (第二個參數)，如果找不到 Key 的值，則返回這個預設值
                user_name = USER_LOCATION_MAP.get(mir_code, mir_code)

                # 關鍵步驟：addItem(顯示中文, 隱藏英文代碼)
                self.cmb_location.addItem(user_name, mir_code)
                self.cmb_location2.addItem(user_name, mir_code)

                user_names_list.append(user_name)
                # 自動補完器
                completer = QCompleter(user_names_list)
                # ✅ 不分大小寫
                completer.setCaseSensitivity(Qt.CaseInsensitive)
                self.cmb_location.setCompleter(completer) 
                self.cmb_location2.setCompleter(completer) 
                
    # 取得全部任務名字
    def load_mission_positions(self):
        self.cmb_mission.clear()
        names = functions.get_mission_id_cmb()
        if names:
            self.cmb_mission.addItems(names)
            completer = QCompleter(names)
            completer.setCaseSensitivity(Qt.CaseInsensitive)
            self.cmb_mission.setCompleter(completer)

    # 取得分類後的每個任務名稱by Mission_groups
    def load_mission_groups_positions(self):
        self.cmb_mission.clear()

        user_names_list = []

        # 獲取 MiR 系統回傳的所有英文代碼列表
        mir_codes_list = functions.get_mission_groups_id_cmb()

        # print("--- 字典 Key 對應診斷 ---")
        # print("MiR 傳回的代碼列表:", mir_codes_list)

        if mir_codes_list:
            for mir_code in mir_codes_list:

                # 【篩選步驟】：只處理你想要的兩種任務代碼
                if mir_code in REQUIRED_MISSION_CODES:

                    # 1. 翻譯：使用你的字典來獲取中文名稱 (Value)
                    # 字典名稱.get(Key,Default Value)。
                    # A (第一個參數)，Python 會嘗試將這個值作為 Key 去字典裡查找；B (第二個參數)，如果找不到 Key 的值，則返回這個預設值
                    user_name = USER_MISSION_GROUP_MAP.get(mir_code, mir_code)
                    
                    # 2. 載入 ComboBox (加蓋)
                    # 顯示給使用者看中文 (user_name)，隱藏 MiR 英文代碼 (mir_code)
                    self.cmb_mission.addItem(user_name, mir_code)

                    user_names_list.append(user_name)
            
            # 自動補完器
            completer = QCompleter(user_names_list)
            # ✅ 不分大小寫
            completer.setCaseSensitivity(Qt.CaseInsensitive)
            self.cmb_mission.setCompleter(completer) 
                

       
 

    ##################################仿射矩陣演算法&畫車位置############################################

    '''根據三個點建立仿射矩陣'''
    def compute_affine_transform(self):
        # A 是 3 個世界座標點，加上一列常數 1，組成 3x3 矩陣
        # 每列為一個點：[x, y, 1]，準備進行仿射轉換
        A = np.hstack([self.world_pts, np.ones((3, 1))])  # world_pts 是 (3x2)，加上 (3x1) → 得到 (3x3)
        # B 是對應的 3 個圖片座標點，每列為一個點：[pixel_x, pixel_y]，共 (3x2)
        B = self.image_pts                                
        # 解 A @ X ≈ B 的最小平方法問題，找出最符合的仿射轉換矩陣 X（3x2）
        # lstsq：least squares 最小平方法 → 會自動幫我們找出誤差最小的解 X
        X, _, _, _ = np.linalg.lstsq(A, B, rcond=None)
        # 回傳 X，就是我們算出來的仿射轉換矩陣（shape 是 3x2）
        return X  # 3x2 矩陣
    
    '''將 MiR 世界座標轉換成圖片像素座標'''
    def world_to_image(self, world_x, world_y):
        # 將輸入的世界座標(x, y) 組成一個向量 [x, y, 1]，shape 是 (1x3)
        input_vec = np.array([world_x, world_y, 1.0])  # 1x3
        # 用仿射矩陣做矩陣乘法，把世界座標轉換成對應的圖片座標 (1x2)
        pixel = input_vec @ self.affine_matrix         # 等同於 np.dot(input_vec, affine_matrix)
        # 回傳轉換後的圖片座標（四捨五入為整數像素位置）
        return int(pixel[0]), int(pixel[1])
    

    '''將 MiR 圖片像素座標轉換成世界座標'''
    def image_to_world(self,pixel_x,pixel_y):
        # 將原本 3x2 的 affine_matrix 補成 3x3，加入 [0, 0, 1] 這一列
        affine_3x3 = np.vstack([self.affine_matrix.T, [0, 0, 1]])  # shape = (3, 3)
        # 計算反矩陣
        inv_affine = np.linalg.inv(affine_3x3)  # shape = (3, 3)
        # 點擊的像素位置向量 [x, y, 1]
        pixel_vec = np.array([pixel_x, pixel_y, 1.0])
        # 做反轉換，取得世界座標
        world_coord = inv_affine @ pixel_vec
        return float(world_coord[0]), float(world_coord[1])
    
    # 畫出車子位置
    def draw_car_position(self,x,y):
        x, y = self.world_to_image(x,y)
        pixmap = self.original_pixmap.copy()
        painter = QPainter(pixmap)
        pen = QPen(QColor("red"))
        pen.setWidth(6)
        painter.setPen(pen)
        radius = 3
        painter.drawEllipse(x - radius, y - radius, radius * 2, radius * 2)
        painter.end()
        self.label_map_1.setPixmap(pixmap)

    # 更新MiR位置
    def update_robot_position(self,world_x,world_y):
        # 畫在地圖上
        self.draw_car_position(world_x,world_y)

    # 自動取得當前MiR車子位置
    def poll_mir_position(self):
        world_x,world_y= functions.check_MiR_status_position()
        # print(f"目前位置：{world_x,world_y}")
        self.update_robot_position(world_x,world_y)

    ##################################跳出錯誤訊息############################################
    def show_error(self,msg):
        #print("我是 QWidget 嗎？", isinstance(self, QWidget))
        QMessageBox.critical(None,"連線錯誤",msg)
    
    
    
    # 偵測滑鼠點擊圖片位置       
    def mousePressEvent(self, event: QMouseEvent): 
            widget = self.childAt(event.pos())  # 取得點擊位置的元件
            if not self.clicked_enabled and widget is self.label_map_1:
                print("尚未啟用點擊模式")
                return
            if widget is self.label_map_1:  # 檢查是否是 QLabel
                relative_pos = self.label_map_1.mapFrom(self, event.pos())
                x = relative_pos.x()/1.48
                y = relative_pos.y()/1.26
                world_x, world_y = self.image_to_world(x, y)
                self.dsb_x_m.setValue(world_x)
                self.dsb_y_m.setValue(world_y)
                print(world_x,world_y)
                # -5.397, 7.455
                # world_x8, world_y8 = self.image_to_world(219, 651)
                # world_x9, world_y9 = self.world_to_image(world_x8,world_y8)
                # print(world_x8, world_y8)
                # print(world_x9, world_y9)
                print(f"你點了圖片座標 ({x:.1f}, {y:.1f})，對應世界座標為 ({world_x:.2f}, {world_y:.2f})")
            super().mousePressEvent(event)
    

app = QApplication()
window = MainWindow()
window.show()
app.exec()