import os
from dotenv import load_dotenv
import pymongo
from pymongo import MongoClient
from pymongo.errors import PyMongoError


class MongoDBManager:
    """
    MongoDB連線管理 (Singleton)

    負責:
        1. 管理資料庫連線
        2. 建立Collection
        3. 建立索引
        4. 錯誤處理
    """

    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance
        
    def _initialize(self):
        """初始化資料庫連線"""
        try:
            load_dotenv()
            MONGODB_URI = os.getenv('MONGODB_URI', "mongodb://localhost:27017")
            
            self.client = MongoClient(MONGODB_URI)
            self.db = self.client.travel_router
            self.planner_records = self.db.planner_records
            self.user_preferences = self.db.user_preferences
            
            self._create_indexes()
            
        except PyMongoError as e:
            print(f"MongoDB連線失敗: {str(e)}")
            raise

    def _create_indexes(self):
        """建立所需的索引"""
        try:
            # 規劃記錄的複合索引
            self.planner_records.create_index([
                ("line_id", pymongo.ASCENDING),
                ("plan_index", pymongo.ASCENDING)
            ], unique=True)

            # 用戶喜好的索引
            self.user_preferences.create_index(
                "line_id", unique=True
            )

        except PyMongoError as e:
            print(f"建立索引失敗: {str(e)}")
            raise
