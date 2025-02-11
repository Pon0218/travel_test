from pymongo import MongoClient
from pymongo.server_api import ServerApi
from typing import Optional, Dict, Any
from dotenv import dotenv_values

from pymongo import MongoClient
from pymongo.server_api import ServerApi
from typing import Optional, Dict, Any
from dotenv import dotenv_values

class MongoDBManage_favorite:
    '''
    MongoDB管理 - Travel Router專案使用
    主要用於管理用戶收藏的地點資訊
    
    使用方式：
    ```python
    # 初始化
    config = dotenv_values(".env")
    mongo_manager = MongoDBManager(config)
    # 新增收藏地點
    add_user("line_user_id", "place_id", place_data)
    # 刪除指定地點
    delete_favorite("line_user_id", "place_id"
    # 修改收藏地點
    fix_favorite("line_user_id", "place_id")
    # 查詢收藏地點
    show_favorite("line_user_id")
    # 確認有無指定用戶
    check_user("line_user_id")
    # 確認用戶是否已收藏該地點
    check_place("line_user_id", "place_id")
    ```
    '''
    
    def __init__(self, config: Dict[str, str]):
        """
        初始化MongoDB連接
        
        Args:
            config: 包含MongoDB連接資訊的配置字典
        """
        self.mongodb_uri = config.get("MONGODB_URI")
        if not self.mongodb_uri:
            raise ValueError("MongoDB URI is required in config")
            
        self.client = MongoClient(self.mongodb_uri, server_api=ServerApi('1'))
        self.db = self.client.travel_router
        self.favorite_collection = self.db.recommend_favorite
        
        # 創建索引以提高查詢效率
        self.favorite_collection.create_index("line_user_id")
        
    def test_connection(self) -> bool:
        """測試數據庫連接是否正常"""
        try:
            self.client.admin.command('ping')
            return True
        except Exception as e:
            print(f"Connection error: {e}")
            return False

    def check_user(self, line_user_id: str) -> bool:
        """
        檢查用戶是否存在於資料庫
        
        Args:
            line_user_id: Line用戶ID
            
        Returns:
            bool: 用戶是否存在
        """
        try:
            return bool(self.favorite_collection.find_one({"line_user_id": line_user_id}))
        except Exception as e:
            print(f"Error checking user: {e}")
            return False

    def check_place(self, line_user_id: str, place_id: str) -> bool:
        """
        檢查特定地點是否已被用戶收藏
        
        Args:
            line_user_id: Line用戶ID
            place_id: 地點ID
            
        Returns:
            bool: 地點是否已被收藏
        """
        try:
            user_doc = self.favorite_collection.find_one({"line_user_id": line_user_id})
            if not user_doc:
                return False
            return place_id in user_doc.get("results", {})
        except Exception as e:
            print(f"Error checking place: {e}")
            return False

    def add_user(self, line_user_id: str, place_id: str, place_data: Dict[str, Any]) -> bool:
        """
        新增用戶和第一個收藏地點到recommend_favorite collection
        
        Args:
            line_user_id: Line用戶ID
            place_id: 地點ID
            place_data: 地點資訊，需包含 name, rating, address, location_url, image_url
            
        Returns:
            bool: 新增是否成功
        """
        try:
            new_doc = {
                "line_user_id": line_user_id,
                "results": {
                    place_id: {
                        "name": place_data["name"],
                        "rating": place_data["rating"],
                        "address": place_data["address"],
                        "location_url": place_data["location_url"],
                        "image_url": place_data["image_url"]
                    }
                }
            }
            self.favorite_collection.insert_one(new_doc)
            return True
        except Exception as e:
            print(f"Error adding user: {e}")
            return False

    def delete_favorite(self, line_user_id: str, place_id: str) -> bool:
        """
        從recommend_favorite collection中刪除指定用戶的特定收藏地點
        
        Args:
            line_user_id: Line用戶ID
            place_id: 要刪除的地點ID
            
        Returns:
            bool: 刪除是否成功
        """
        try:
            # 使用unset操作來移除特定的place_id
            result = self.favorite_collection.update_one(
                {"line_user_id": line_user_id},
                {"$unset": {f"results.{place_id}": ""}}
            )
            
            if result.modified_count > 0:
                print(f"Successfully deleted place {place_id} for user {line_user_id}")
                
                # 檢查用戶是否還有其他收藏
                user_doc = self.favorite_collection.find_one({"line_user_id": line_user_id})
                if user_doc and len(user_doc.get("results", {})) == 0:
                    # 如果沒有其他收藏了，刪除整個文檔
                    self.favorite_collection.delete_one({"line_user_id": line_user_id})
                    print(f"Removed empty document for user {line_user_id}")
                    
                return True
            else:
                print(f"No matching place found for user {line_user_id} and place {place_id}")
                return False

        except Exception as e:
            print(f"Error deleting favorite: {e}")
            return False

    def fix_favorite(self, line_user_id: str, place_id: str, place_data: Dict[str, Any]) -> bool:
        """
        更新用戶的收藏地點清單，最多保存10個地點
        
        Args:
            line_user_id: Line用戶ID
            place_id: 地點ID
            place_data: 地點資訊，需包含 name, rating, address, location_url, image_url
            
        Returns:
            bool: 更新是否成功
        """
        try:
            user_doc = self.favorite_collection.find_one({"line_user_id": line_user_id})
            if not user_doc:
                print(f"User {line_user_id} not found")
                return False
                
            current_results = user_doc.get("results", {})
            
            # 如果該地點已存在，返回False
            if place_id in current_results:
                return False
                
            # 如果收藏數達到上限，刪除最舊的一個
            if len(current_results) >= 10:
                oldest_place_id = next(iter(current_results.keys()))
                self.favorite_collection.update_one(
                    {"line_user_id": line_user_id},
                    {"$unset": {f"results.{oldest_place_id}": ""}}
                )
            
            # 新增新的收藏
            self.favorite_collection.update_one(
                {"line_user_id": line_user_id},
                {"$set": {f"results.{place_id}": {
                    "name": place_data["name"],
                    "rating": place_data["rating"],
                    "address": place_data["address"],
                    "location_url": place_data["location_url"],
                    "image_url": place_data["image_url"]
                }}}
            )
            return True
            
        except Exception as e:
            print(f"Error updating favorite: {e}")
            return False

    def show_favorite(self, line_user_id: str) -> Optional[Dict]:
        """
        取得用戶收藏的地點清單
        
        Args:
            line_user_id: Line用戶ID
            
        Returns:
            Optional[Dict]: 用戶的收藏results，若用戶不存在則返回None
        """
        try:
            user_doc = self.favorite_collection.find_one({"line_user_id": line_user_id})
            return user_doc.get("results") if user_doc else None
                
        except Exception as e:
            print(f"Error retrieving favorites: {e}")
            return None

    def close(self):
        """關閉數據庫連接"""
        self.client.close()

# 使用示例
if __name__ == "__main__":
    # 載入環境變量
    config = dotenv_values(".env")
    
    try:
        mongodb_obj = MongoDBManage_favorite(config)
        
        if mongodb_obj.test_connection():
            print("Successfully connected to MongoDB!")
            
            # 測試添加收藏
            test_place = {
                "name": "星巴克信義門市",
                "rating": 4.5,
                "address": "台北市信義區信義路五段7號",
                "location_url": "https://maps.google.com/?q=place_id:ChIJxxxxxx",
                "image_url": "https://example.com/image1.jpg"
            }
            
            success = mongodb_obj.add_favorite("U123456789", "ChIJxxxxxx", test_place)
            if success:
                print("Successfully added favorite!")
            else:
                print("Failed to add favorite or user already exists")
            
            # 測試刪除收藏
            # delete_success = mongodb_obj.delete_favorite("U123456789", "ChIJxxxxxx")
            # if delete_success:
            #     print("Successfully deleted favorite!")
            # else:
            #     print("Failed to delete favorite")
                
    finally:
        mongodb_obj.close()