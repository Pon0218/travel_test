import pytest
from datetime import datetime

from feature.nosql_mongo.mongo_trip.mongodb_handler import TripDBHandler


@pytest.fixture
def db_handler():
    """建立資料庫handler"""
    return TripDBHandler()


@pytest.fixture
def test_line_id():
    """測試用的LINE ID"""
    return "test_user_id"


@pytest.fixture
def test_plan_data():
    """測試用的規劃資料"""
    return {
        "input_text": "我想去台北玩",
        "requirement": {
            "start_time": "09:00",
            "end_time": "21:00",
            "transport_mode": "driving"
        },
        "itinerary": [
            {
                "step": 1,
                "name": "台北101",
                "start_time": "10:00",
                "end_time": "12:00"
            }
        ]
    }


@pytest.fixture(autouse=True)
def cleanup(db_handler, test_line_id):
    """每次測試後清理資料"""
    yield
    db_handler.clear_user_data(test_line_id)


def test_record_user_input(db_handler, test_line_id):
    """測試記錄用戶輸入"""
    # 記錄輸入
    result = db_handler.record_user_input(
        line_id=test_line_id,
        input_text="我想去台北玩"
    )
    assert result is True

    # 確認記錄
    history = db_handler.get_input_history(test_line_id)
    assert len(history) == 1
    assert history[0]["text"] == "我想去台北玩"
    assert "timestamp" in history[0]

    print("\n成功記錄用戶輸入:")
    print(f"輸入歷史: {history}")


def test_save_plan(db_handler, test_line_id, test_plan_data):
    """測試儲存規劃記錄"""
    # 儲存規劃
    plan_index = db_handler.save_plan(
        line_id=test_line_id,
        input_text=test_plan_data["input_text"],
        requirement=test_plan_data["requirement"],
        itinerary=test_plan_data["itinerary"]
    )

    assert plan_index is not None
    assert isinstance(plan_index, int)
    assert plan_index > 0

    print(f"\n成功儲存規劃記錄, plan_index: {plan_index}")


def test_get_latest_plan(db_handler, test_line_id, test_plan_data):
    """測試取得最新規劃"""
    # 先儲存兩筆規劃
    db_handler.save_plan(
        line_id=test_line_id,
        input_text="第一次規劃",
        requirement=test_plan_data["requirement"],
        itinerary=test_plan_data["itinerary"]
    )

    db_handler.save_plan(
        line_id=test_line_id,
        input_text="第二次規劃",
        requirement=test_plan_data["requirement"],
        itinerary=test_plan_data["itinerary"]
    )

    # 取得最新規劃
    latest_plan = db_handler.get_latest_plan(test_line_id)

    assert latest_plan is not None
    assert latest_plan["input_text"] == "第二次規劃"
    assert latest_plan["plan_index"] == 2

    print("\n成功取得最新規劃:")
    print(f"規劃內容: {latest_plan}")


def test_get_plan_by_index(db_handler, test_line_id, test_plan_data):
    """測試根據索引取得規劃"""
    # 儲存規劃
    plan_index = db_handler.save_plan(
        line_id=test_line_id,
        input_text=test_plan_data["input_text"],
        requirement=test_plan_data["requirement"],
        itinerary=test_plan_data["itinerary"]
    )

    # 用index取得規劃
    plan = db_handler.get_plan_by_index(test_line_id, plan_index)

    assert plan is not None
    assert plan["plan_index"] == plan_index
    assert plan["input_text"] == test_plan_data["input_text"]

    print("\n成功取得指定規劃:")
    print(f"規劃內容: {plan}")


def test_multiple_inputs(db_handler, test_line_id):
    """測試多次輸入記錄"""
    # 記錄多筆輸入
    inputs = [
        "我想去台北玩",
        "不要太多人的地方",
        "想要文青風格"
    ]

    for text in inputs:
        db_handler.record_user_input(test_line_id, text)

    # 取得歷史記錄
    history = db_handler.get_input_history(test_line_id)

    assert len(history) == len(inputs)
    for i, record in enumerate(history):
        assert record["text"] == inputs[i]

    print("\n成功記錄多筆輸入:")
    print(f"輸入歷史: {history}")


def test_clear_user_data(db_handler, test_line_id, test_plan_data):
    """測試清除用戶資料"""
    # 先新增一些資料
    db_handler.record_user_input(test_line_id, "測試輸入")
    db_handler.save_plan(
        line_id=test_line_id,
        input_text=test_plan_data["input_text"],
        requirement=test_plan_data["requirement"],
        itinerary=test_plan_data["itinerary"]
    )

    # 清除資料
    result = db_handler.clear_user_data(test_line_id)
    assert result is True

    # 確認資料已清除
    history = db_handler.get_input_history(test_line_id)
    latest_plan = db_handler.get_latest_plan(test_line_id)

    assert len(history) == 0
    assert latest_plan is None

    print("\n成功清除用戶資料")


if __name__ == "__main__":
    pytest.main(["-v", "-s", __file__])
