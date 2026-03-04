from TaskDBManager import TaskDBManager
from utils import hash_password
class UserDBManager(TaskDBManager):
    def initialize_user_table(self):
        """
        確保資料庫環境健全，並初始化必要的預設帳號

        功能：
        1. 確保在資料庫中植入或保留一個超級管理者 (admin) 帳號。
        """

        admin_hash = hash_password("admin123") 

        # - 如果資料庫中已經存在 username='admin' 的記錄，則忽略本次 INSERT。
        # - 這樣可以保證：只有在第一次執行時會建立 admin 帳號，後續執行不會覆蓋使用者修改過的新密碼。
        insert_admin_query = """
        INSERT INTO users (username, password_hash, is_admin)
        VALUES ('admin', %s, TRUE)
        ON CONFLICT (username) DO NOTHING; -- 避免重複插入
        """
        self._execute_query(insert_admin_query, (admin_hash,), commit=True)
        print("✅ admin 帳號檢查完成。")

    # 取得使用者密碼
    # -> str | None，函式執行後，返回的值可能是 None 或是一個字典
    def get_user_password_hash(self, username:str) -> str | None:
        """根據帳號取得密碼 Hash"""
        query = "SELECT password_hash FROM users WHERE username = %s;"
        result = self._execute_query(query, (username,), fetch=True)
        if result:
            return result[0]["password_hash"]
        return None
    
    # 取得所有使用者帳號
    def get_all_usernames(self) -> list[str]:
        query = "SELECT username FROM users ORDER BY username ASC;"
        result = self._execute_query(query, fetch=True)
        return [row['username'] for row in result]
    
    # 新增使用者
    def add_new_user(self, username:str, password_hash:str):
        query = "INSERT INTO users (username, password_hash) VALUES (%s, %s);"
        try:
            self._execute_query(query, (username, password_hash), commit=True)
            print(f"✅ 使用者帳號 {username} 已新增。")
            return True
        except Exception as e:
            print(f"❌ 使用者帳號 {username} 新增失敗：{e}")
            return False

    # 刪除使用者
    def delete_user(self, username:str):
        query = "DELETE FROM users where username = %s;"
        try:
            self._execute_query(query, (username,), commit=True)
            print(f"✅ 使用者帳號 {username} 已刪除。")
        except Exception as e:
            print(f"❌ 使用者帳號 {username} 刪除失敗：{e}")    

    # 修改使用者密碼
    def update_user_password(self, username:str, new_password_hash:str):
        query = "UPDATE users SET password_hash = %s WHERE username = %s;"
        try:
            self._execute_query(query, (new_password_hash, username), commit=True)
            print(f"✅ 使用者帳號 {username} 的密碼已更新。")
        except Exception as e:
            print(f"❌ 使用者帳號 {username} 的密碼更新失敗：{e}")