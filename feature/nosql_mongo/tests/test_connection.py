import pytest
from pymongo import MongoClient
from pymongo.errors import PyMongoError
import os
from dotenv import load_dotenv


def test_mongodb_connection():
    """測試MongoDB連線並列出資料庫資訊"""
    try:
        # 載入環境變數
        load_dotenv()
        MONGODB_URI = os.getenv('MONGODB_URI') or "mongodb://localhost:27017"

        # 建立連線
        client = MongoClient(MONGODB_URI)

        # 測試連線
        client.server_info()
        print("\n成功連線到MongoDB!")

        # 列出所有資料庫
        databases = client.list_database_names()
        print("\n=== 資料庫列表 ===")
        for db in databases:
            print(f"- {db}")

            # 列出該資料庫的collections
            db_instance = client[db]
            collections = db_instance.list_collection_names()

            if collections:
                print("  Collections:")
                for collection in collections:
                    # 取得該collection的文件數量
                    count = db_instance[collection].count_documents({})
                    print(f"    * {collection} (文件數: {count})")
            else:
                print("  無collections")

        print("\n=== 連線資訊 ===")
        print(f"連線字串: {MONGODB_URI}")

    except PyMongoError as e:
        pytest.fail(f"MongoDB連線失敗: {str(e)}")


if __name__ == "__main__":
    pytest.main(["-v", "-s", __file__])
