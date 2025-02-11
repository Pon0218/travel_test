# MongoDB使用說明

## 架構
```
feature/nosql_mongo/mongo_trip
  ├── mongodb_manager.py  - 資料庫連線管理(singleton)
  ├── mongodb_handler.py  - CRUD操作實作
  ├── db_helper.py       - 簡單存取介面
  └── __init__.py        - 匯出trip_db實例
```

## 基本使用
```python
# 在需要使用資料庫的地方
from feature.nosql import trip_db

# 記錄用戶輸入
trip_db.record_user_input(
    line_id="USER_LINE_ID",
    input_text="用戶說的話"
)

# 儲存規劃結果
trip_db.save_plan(
    line_id="USER_LINE_ID",
    input_text="觸發規劃的輸入",
    requirement={
        "start_time": "09:00",
        "end_time": "21:00",
        "transport_mode": "driving"
    },
    itinerary=[
        {
            "step": 1,
            "name": "台北101",
            "start_time": "10:00",
            "end_time": "12:00"
        }
    ]
)

# 取得歷史記錄
history = trip_db.get_input_history("USER_LINE_ID")

# 取得最新規劃
latest_plan = trip_db.get_latest_plan("USER_LINE_ID")
```

## 資料結構

### user_preferences Collection
```json
{
    "line_id": "用戶LINE ID",
    "input_history": [
        {
            "timestamp": "ISODate(時間戳記)",
            "text": "用戶輸入文字"
        }
    ]
}
```

### planner_records Collection
```json
{
    "line_id": "用戶LINE ID",
    "plan_index": 1,  # 第幾次規劃
    "timestamp": "ISODate(時間戳記)",
    "input_text": "觸發規劃的輸入",
    "requirement": {
        "start_time": "09:00",
        "end_time": "21:00", 
        "transport_mode": "driving"
        # 其他規劃需求
    },
    "itinerary": [
        {
            "step": 1,
            "name": "地點名稱",
            "start_time": "10:00",
            "end_time": "12:00"
            # 其他行程資訊
        }
    ]
}
```

## 主要功能

### 1. 記錄用戶輸入
```python
trip_db.record_user_input(line_id, input_text)
```
- 每次用戶傳訊息時呼叫
- 自動記錄時間戳記

### 2. 儲存規劃
```python
plan_index = trip_db.save_plan(
    line_id,
    input_text,
    requirement,
    itinerary
)
```
- 規劃完成時呼叫
- 會自動產生plan_index
- 回傳新的plan_index

### 3. 取得輸入歷史
```python
history = trip_db.get_input_history(line_id)
```
- 回傳用戶所有輸入記錄
- 依時間排序

### 4. 取得規劃記錄
```python
# 最新規劃
latest = trip_db.get_latest_plan(line_id)

# 指定規劃
plan = trip_db.get_plan_by_index(line_id, plan_index)
```

### 5. 清除資料(測試用)
```python
trip_db.clear_user_data(line_id)
```
- 清除該用戶的所有資料
- 包含輸入歷史和規劃記錄

## 注意事項
1. 不需要手動初始化trip_db
2. line_id來自Line事件的user_id
3. 所有時間都用UTC儲存
4. 異常會記錄到log
5. 資料會自動建立索引

## 測試
```bash
# 在tests目錄執行
pytest test_connection.py -v -s
pytest test_crud.py -v -s
```