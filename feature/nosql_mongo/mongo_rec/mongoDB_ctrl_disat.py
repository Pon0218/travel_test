from pymongo import MongoClient
from pymongo.server_api import ServerApi
from typing import Optional, Dict, Any, Set, List
from dotenv import dotenv_values
from datetime import datetime

class MongoDBManage_unsatisfied:
    '''
    MongoDB管理 - Travel Router專案使用
    主要用於管理用戶對推薦不滿意的記錄，包含黑名單管理和查詢記錄存儲
    
    使用方式：
    ```python
    # 初始化
    config = dotenv_values(".env")
    mongo_manager = MongoDBManage_unsatisfied(config)
    
    # 檢查用戶是否存在
    exists = mongo_manager.check_user_exists("Uxxxx")
    
    # 新增不滿意記錄
    mongo_manager.add_unsatisfied(query_info)
    
    # 更新黑名單（當用戶點擊再推薦時）
    mongo_manager.update_blacklist("Uxxxx", ["place1", "place2", ...])
    
    # 比對用戶查詢是否相同
    mongo_manager.compare_query(query_info)
    
    # 更新用戶查詢資訊
    mongo_manager.update_query_info(query_info)
    
    # 獲取用戶所有記錄
    user_records = mongo_manager.get_user_records("Uxxxx")
    
    #刪除用戶所有紀錄
    delete_user_record(line_user_id)
    # 關閉連接
    mongo_manager.close()
    ```
    '''
    
    def __init__(self, config: Dict[str, str]):
        """初始化MongoDB連接"""
        self.mongodb_uri = config.get("MONGODB_URI")
        if not self.mongodb_uri:
            raise ValueError("MongoDB URI在設定中是必要的")
            
        self.client = MongoClient(self.mongodb_uri, server_api=ServerApi('1'))
        self.db = self.client.travel_router
        self.unsatisfied_collection = self.db.recommend_unsatisfied
        
        # 創建索引以提高查詢效率
        self.unsatisfied_collection.create_index([("line_user_id", 1)])

    def test_connection(self) -> bool:
        """測試數據庫連接是否正常"""
        try:
            self.client.admin.command('ping')
            return True
        except Exception as e:
            print(f"連接錯誤: {e}")
            return False

    def add_unsatisfied(self, query_info: Dict[str, Any]) -> bool:
        """
        新增用戶的不滿意記錄
        
        參數:
            query_info: 包含所有查詢相關資訊的字典
            
        回傳:
            bool: 新增是否成功
        """
        try:
            # 將 black_list 轉換為 list，因為 MongoDB 不支援 set 類型
            query_info["black_list"] = list(query_info.get("black_list", []))
            
            # 插入文檔
            self.unsatisfied_collection.insert_one(query_info)
            return True
            
        except Exception as e:
            print(f"新增不滿意記錄時發生錯誤: {e}")
            return False

    def update_blacklist(self, line_user_id: str, place_ids: List[str]) -> bool:
        """
        更新用戶的黑名單，將新的 place_ids 加入到現有黑名單中
        
        參數:
            line_user_id: Line用戶ID
            place_ids: 要加入黑名單的地點ID列表
                
        回傳:
            bool: 更新是否成功
        """
        try:
            # 取得現有黑名單
            user_record = self.unsatisfied_collection.find_one(
                {"line_user_id": line_user_id}
            )
            if not user_record:
                print(f"找不到用戶 {line_user_id} 的記錄")
                return False
            
            # 合併現有和新的黑名單
            current_blacklist = set(user_record.get("black_list", []))
            new_blacklist = current_blacklist.union(place_ids)
            
            # 更新到資料庫
            result = self.unsatisfied_collection.update_one(
                {"line_user_id": line_user_id},
                {"$set": {"black_list": list(new_blacklist)}}
            )
            
            success = result.modified_count > 0
            if success:
                print(f"用戶 {line_user_id} 的黑名單更新成功，共 {len(new_blacklist)} 個地點")
            else:
                print(f"用戶 {line_user_id} 的黑名單無變化")
                
            return success
                
        except Exception as e:
            print(f"更新黑名單時發生錯誤: {e}")
            return False

    def compare_query(self, query_info: Dict[str, Any]) -> bool:
        """
        比對用戶輸入的query和資料庫中已存在的query是否相同
        
        參數:
            query_info: 包含查詢相關資訊的字典
            
        回傳:
            bool: 如果查詢相同返回True，否則返回False
        """
        try:
            # 獲取必要資訊
            line_user_id = query_info["line_user_id"]
            new_query = query_info["query"]
            
            # 找到該用戶的記錄
            user_record = self.unsatisfied_collection.find_one({
                "line_user_id": line_user_id
            })
            
            if not user_record:
                return False
                
            # 比對query是否相同
            existing_query = user_record.get("query", "")
            return existing_query == new_query
            
        except Exception as e:
            print(f"比對查詢時發生錯誤: {e}")
            return False

    def update_query_info(self, query_info: Dict[str, Any]) -> bool:
        """
        使用新的 query_info 完整覆蓋更新用戶的記錄
        
        參數:
            query_info: 包含完整查詢資訊的字典
            
        回傳:
            bool: 更新是否成功
        """
        try:
            line_user_id = query_info["line_user_id"]
            
            # 直接用新的 query_info 替換舊記錄
            result = self.unsatisfied_collection.update_one(
                {"line_user_id": line_user_id},
                {"$set": query_info},
                upsert=True  # 如果不存在則創建新記錄
            )
            
            success = result.modified_count > 0 or result.upserted_id is not None
            if success:
                print(f"成功更新用戶 {line_user_id} 的查詢記錄")
            else:
                print(f"用戶 {line_user_id} 的查詢記錄無變化")
                
            return success
            
        except Exception as e:
            print(f"更新查詢記錄時發生錯誤: {e}")
            return False

    def check_user_exists(self, line_user_id: str) -> bool:
        """
        檢查用戶是否存在於資料庫中
        
        參數:
            line_user_id: Line用戶ID
            
        回傳:
            bool: 用戶是否存在
        """
        try:
            result = self.unsatisfied_collection.find_one(
                {"line_user_id": line_user_id}
            )
            
            return result is not None
            
        except Exception as e:
            print(f"檢查用戶存在時發生錯誤: {e}")
            return False

    def get_user_records(self, line_user_id: str) -> List[Dict[str, Any]]:
        """
        獲取指定用戶的所有記錄
        
        參數:
            line_user_id: Line用戶ID
            
        回傳:
            List[Dict[str, Any]]: 該用戶的所有記錄列表
        """
        try:
            # 查詢該用戶的記錄
            records = list(self.unsatisfied_collection.find(
                {"line_user_id": line_user_id}
            ))
            
            if records:
                # 將 _id 轉換為字符串
                for record in records:
                    record['_id'] = str(record['_id'])
                return records
            
            return []
            
        except Exception as e:
            print(f"獲取用戶記錄時發生錯誤: {e}")
            return []

    def delete_user_record(self, line_user_id: str) -> bool:
        """
        刪除指定用戶的所有記錄
        
        參數:
            line_user_id: Line用戶ID
                
        回傳:
            bool: 刪除是否成功
        """
        try:
            # 刪除該用戶的所有記錄
            result = self.unsatisfied_collection.delete_many(
                {"line_user_id": line_user_id}
            )
            
            success = result.deleted_count > 0
            if success:
                print(f"成功刪除用戶 {line_user_id} 的所有記錄")
            else:
                print(f"用戶 {line_user_id} 無記錄可刪除")
                
            return success
            
        except Exception as e:
            print(f"刪除用戶記錄時發生錯誤: {e}")
            return False    
    def close(self):
        """關閉數據庫連接"""
        self.client.close()


# 測試用例
if __name__ == "__main__":
    # 載入環境變量
    config = dotenv_values(".env")
    
    try:
        mongodb_obj = MongoDBManage_unsatisfied(config)
        
        if mongodb_obj.test_connection():
            print("成功連接到 MongoDB!")
            
            # 測試新增記錄
            test_query_info = {
                "line_user_id": "U123456789",
                "query": "推薦台北咖啡廳",
                "query_of_llm": "用戶想找一間環境舒適的咖啡廳",
                "special_requirement": {
                    "內用座位": True,
                    "wi-fi": True
                },
                "user_requirement": {
                    "類別": "咖啡廳",
                    "預算": 500
                },
                "black_list": set()
            }
            
            # if mongodb_obj.add_unsatisfied(test_query_info):
            #     print("成功新增記錄!")
                
            #     # 測試更新黑名單
            #     test_place_ids = [f"place{i}" for i in range(1, 11)]
            #     if mongodb_obj.update_blacklist("U123456789", test_place_ids):
            #         print("成功更新黑名單!")
                
    finally:
        mongodb_obj.close()