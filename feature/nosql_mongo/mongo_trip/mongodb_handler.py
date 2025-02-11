from datetime import datetime, UTC
from typing import Dict, List, Optional
from zoneinfo import ZoneInfo

import pymongo
from pymongo.errors import PyMongoError
from feature.nosql_mongo.mongo_trip.mongodb_manager import MongoDBManager


class TripDBHandler:
    """旅遊行程資料庫操作處理器

    負責:
    1. 記錄用戶輸入
    2. 儲存行程規劃
    3. 查詢歷史記錄 
    4. 錯誤處理
    """

    def __init__(self):
        """初始化,取得資料庫連線"""
        self.db = MongoDBManager()

    def record_user_input(
        self,
        line_id: str,
        input_text: str
    ) -> bool:
        """記錄用戶輸入

        Args:
            line_id: LINE用戶ID
            input_text: 用戶輸入文字

        Returns:
            bool: 是否成功記錄
        """
        try:
            skip_messages = [
                "收藏店家:",
                "顯示我的收藏",
                "推薦其他店家",
                "我想進行情境搜索",
                "情境搜索說明",
                "旅遊規劃說明",
                "紀錄初始化",
                "記錄初始化",
                "移除",
                "推薦其他店家",
            ]

            if any(input_text.startswith(msg) for msg in skip_messages):
                return False  # 直接返回,不記錄

            if input_text.startswith("旅遊推薦") and len(input_text) > 4:
                input_text = input_text[4:]

            input_record = {
                "timestamp": datetime.now(ZoneInfo('Asia/Taipei')),
                "text": input_text if input_text.startswith("旅遊推薦") else input_text
            }

            result = self.db.user_preferences.update_one(
                {"line_id": line_id},
                {"$push": {"input_history": input_record}},
                upsert=True
            )

            return result.modified_count > 0 or result.upserted_id is not None

        except PyMongoError as e:
            print(f"記錄用戶輸入失敗: {str(e)}")
            return False

    def update_user_dislike(
        self,
        line_id: str,
        dislike_reason: str
    ) -> bool:
        """更新用戶不喜歡的項目

        Args:
            line_id: 用戶ID
            dislike_reason: 不喜歡的原因(例如:"我不喜歡遼寧街夜市(夜市)")

        Returns:
            bool: 是否更新成功
        """
        try:
            # 將新的不喜歡原因加入偏好列表
            result = self.db.user_preferences.update_one(
                {"line_id": line_id},
                {
                    "$push": {
                        "input_history": {
                            "timestamp": datetime.now(ZoneInfo('Asia/Taipei')),
                            "text": dislike_reason
                        }
                    }
                },
                upsert=True
            )
            return result.modified_count > 0 or result.upserted_id is not None

        except PyMongoError as e:
            print(f"更新用戶偏好失敗: {str(e)}")
            return False

    def update_plan_restart_index(
        self,
        line_id: str,
        plan_index: int,
        restart_index: int,
        button_id: str
    ) -> bool:
        try:
            record = self.db.planner_records.find_one({
                "line_id": line_id,
                "plan_index": plan_index,
            })

            if not record:
                print(f"找不到行程記錄 plan_index={plan_index}")
                return False

            print(f"目前record: {record}")  # debug記錄

            if "clicked_buttons" not in record:
                self.db.planner_records.update_one(
                    {"line_id": line_id, "plan_index": plan_index},
                    {"$set": {"clicked_buttons": []}}
                )
                print("初始化clicked_buttons陣列")

            if button_id in record.get("clicked_buttons", []):
                print(f"按鈕 {button_id} 已經按過")
                return False

            current_restart = record.get('restart_index', float('inf'))
            print(f"比較 current: {current_restart}, new: {restart_index}")

            update_data = {
                "$push": {"clicked_buttons": button_id}
            }

            if restart_index < current_restart:
                update_data["$set"] = {
                    "restart_index": restart_index,
                    "updated_at": datetime.now(ZoneInfo('Asia/Taipei'))
                }
                print(f"更新 restart_index 為 {restart_index}")

            result = self.db.planner_records.update_one(
                {"line_id": line_id, "plan_index": plan_index},
                update_data
            )
            return result.modified_count > 0

        except PyMongoError as e:
            print(f"更新重啟點失敗: {str(e)}")
            return False

    def save_plan(
        self,
        line_id: str,
        input_text: str,
        requirement: Dict,
        itinerary: List[Dict]
    ) -> Optional[int]:
        """儲存行程規劃

        Args:
            line_id: LINE用戶ID 
            input_text: 觸發規劃的輸入文字
            restart_index: 重新規劃的索引
            requirement: 規劃需求
            itinerary: 規劃行程

        Returns:
            Optional[int]: 新規劃的index,失敗時返回None
        """
        try:
            # 取得新的plan_index
            last_record = self.db.planner_records.find_one(
                {"line_id": line_id},
                sort=[("plan_index", pymongo.DESCENDING)]
            )
            new_index = 1 if not last_record else last_record["plan_index"] + 1

            # 建立規劃記錄
            record = {
                "line_id": line_id,
                "plan_index": new_index,
                "timestamp": datetime.now(ZoneInfo('Asia/Taipei')),
                "input_text": input_text,
                "requirement": requirement,
                # "restart_index": restart_index,
                "itinerary": [{
                    "step": item["step"],
                    "place_id": item["place_id"],
                    "date": item["date"],
                    "name": item["name"],
                    "label": item["label"],
                    "lat": item["lat"],
                    "lon": item["lon"],
                    "period": item["period"],
                    "start_time": item["start_time"],
                    "end_time": item["end_time"],
                    "hours": item["hours"],
                    "transport": item["transport"],
                    "duration": item["duration"]
                } for item in itinerary]
            }

            self.db.planner_records.insert_one(record)
            return new_index

        except PyMongoError as e:
            print(f"儲存規劃記錄失敗: {str(e)}")
            return None

    def get_input_history(
        self,
        line_id: str
    ) -> List[Dict]:
        """取得用戶輸入歷史

        Args:
            line_id: LINE用戶ID

        Returns:
            List[Dict]: 輸入記錄列表,依時間排序
        """
        try:
            user_prefs = self.db.user_preferences.find_one(
                {"line_id": line_id})
            if not user_prefs or "input_history" not in user_prefs:
                return []

            return sorted(
                user_prefs["input_history"],
                key=lambda x: x["timestamp"]
            )

        except PyMongoError as e:
            print(f"取得輸入歷史失敗: {str(e)}")
            return []

    def get_latest_plan(
        self,
        line_id: str
    ) -> Optional[Dict]:
        """取得用戶最新的規劃記錄

        Args:
            line_id: LINE用戶ID

        Returns:
            Optional[Dict]: 最新規劃記錄,無記錄時返回None
        """
        try:
            return self.db.planner_records.find_one(
                {"line_id": line_id},
                sort=[("plan_index", pymongo.DESCENDING)]
            )
        except PyMongoError as e:
            print(f"取得最新規劃失敗: {str(e)}")
            return None

    def get_plan_by_index(
        self,
        line_id: str,
        plan_index: int
    ) -> Optional[Dict]:
        """根據索引取得特定規劃記錄

        Args:
            line_id: LINE用戶ID
            plan_index: 規劃索引

        Returns:
            Optional[Dict]: 對應的規劃記錄,無記錄時返回None
        """
        try:
            return self.db.planner_records.find_one({
                "line_id": line_id,
                "plan_index": plan_index
            })
        except PyMongoError as e:
            print(f"取得規劃記錄失敗: {str(e)}")
            return None

    def get_history_status(
        self,
        line_id: str,
        count_threshold: int = 10
    ) -> Dict:
        """取得歷史紀錄狀態

        Returns:
            Dict: {
                "summary": str,            # 上次整理的摘要,沒有則None 
                "new_messages": List[str], # 新對話列表
                "needs_summary": bool,     # 是否需要整理(超過門檻或沒整理過)
                "last_summary_time": datetime # 上次整理時間,沒有則None
            }
        """
        try:
            user = self.db.user_preferences.find_one({"line_id": line_id})
            if not user:
                return {
                    "summary": None,
                    "new_messages": [],
                    "needs_summary": False,
                    "last_summary_time": None
                }

            summary = user.get("preferences_summary")
            last_time = user.get("last_summary_time")
            messages = user.get("input_history", [])

            # 取得最後整理後的對話
            new_messages = (
                messages if not last_time
                else [m for m in messages if m["timestamp"] > last_time]
            )

            needs_summary = (
                len(new_messages) >= count_threshold or
                not last_time  # 沒整理過也要整理
            )

            return {
                "summary": summary,
                "new_messages": new_messages,
                "needs_summary": needs_summary,
                "last_summary_time": last_time
            }
        except Exception as e:
            print(f"取得歷史狀態失敗: {str(e)}")
            return None

    def update_summary(
        self,
        line_id: str,
        summary: str
    ) -> bool:
        """更新歷史摘要

        Args:
            line_id: 用戶ID
            summary: 整理後的摘要

        Returns:
            bool: 是否成功
        """
        try:
            result = self.db.user_preferences.update_one(
                {"line_id": line_id},
                {
                    "$set": {
                        "preferences_summary": summary,
                        "last_summary_time": datetime.now(ZoneInfo('Asia/Taipei'))
                    }
                },
                upsert=True
            )
            return result.modified_count > 0 or result.upserted_id is not None
        except Exception as e:
            print(f"更新摘要失敗: {str(e)}")
            return False

    def clear_user_data(
        self,
        line_id: str
    ) -> bool:
        """清除用戶所有資料(測試用)

        Args:
            line_id: LINE用戶ID

        Returns:
            bool: 是否成功清除
        """
        try:
            # 刪除規劃記錄
            self.db.planner_records.delete_many({"line_id": line_id})
            # 刪除用戶偏好
            self.db.user_preferences.delete_one({"line_id": line_id})
            return True

        except PyMongoError as e:
            print(f"清除用戶資料失敗: {str(e)}")
            return False
