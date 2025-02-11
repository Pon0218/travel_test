import pytest
from datetime import datetime
import warnings

from feature.nosql_mongo import trip_db

warnings.filterwarnings("ignore", category=pytest.PytestAssertRewriteWarning)


def test_db_connection():
    """測試資料庫連線和基本操作"""
    try:
        # 測試用資料
        test_line_id = "test_connection_user"
        test_input = "測試輸入文字"

        # 1. 測試記錄輸入
        result = trip_db.record_user_input(
            line_id=test_line_id,
            input_text=test_input
        )
        assert result is True
        print("\n成功記錄測試輸入")

        # 2. 測試讀取歷史
        history = trip_db.get_input_history(test_line_id)
        assert len(history) > 0
        assert history[-1]["text"] == test_input
        print(f"\n成功讀取輸入歷史: {history}")

        # 3. 測試儲存規劃
        test_plan = {
            "requirement": {
                "start_time": "09:00",
                "end_time": "18:00"
            },
            "itinerary": [{
                "step": 1,
                "name": "測試景點"
            }]
        }

        plan_index = trip_db.save_plan(
            line_id=test_line_id,
            input_text=test_input,
            requirement=test_plan["requirement"],
            itinerary=test_plan["itinerary"]
        )

        assert plan_index is not None
        print(f"\n成功儲存測試規劃, plan_index: {plan_index}")

        # 4. 測試讀取規劃
        saved_plan = trip_db.get_latest_plan(test_line_id)
        assert saved_plan is not None
        assert saved_plan["input_text"] == test_input
        print(f"\n成功讀取最新規劃: {saved_plan}")

        # 5. 清理測試資料
        trip_db.clear_user_data(test_line_id)
        print("\n清理測試資料完成")

    except Exception as e:
        pytest.fail(f"資料庫操作測試失敗: {str(e)}")


def test_input_history_format():
    """測試輸入歷史格式"""
    test_line_id = "test_format_user"
    try:
        # 儲存測試輸入
        trip_db.record_user_input(test_line_id, "測試格式")

        # 讀取歷史
        history = trip_db.get_input_history(test_line_id)

        # 檢查格式
        assert len(history) > 0
        last_record = history[-1]

        assert "text" in last_record
        assert "timestamp" in last_record
        assert isinstance(last_record["text"], str)
        assert isinstance(last_record["timestamp"], datetime)

        print("\n輸入歷史格式正確:")
        print(last_record)

    except Exception as e:
        pytest.fail(f"格式測試失敗: {str(e)}")
    finally:
        # 清理資料
        trip_db.clear_user_data(test_line_id)


if __name__ == "__main__":
    pytest.main(["-v", "-s", __file__])
