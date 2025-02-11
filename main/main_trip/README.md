# Main Trip Module Documentation

## Overview
根據使用者輸入自動規劃台北一日遊行程,包含景點及餐廳推薦。

## 功能特色
- 自然語言輸入與歷史紀錄整合
- 智慧用餐時段規劃 
- 針對性重新規劃
- 使用者喜好記憶
- 交通時間估算

## 使用方法

### Basic Usage

```python
from main.main_trip.controllers.controller import TripController, init_config

# 建立控制器實例
controller = TripController(init_config())

# 處理使用者輸入
user_input = "想去台北文青的地方，吃午餐要便宜又好吃，下午想去逛有特色的景點，晚餐要可以跟朋友聚餐"
result = controller.process_message(
    text="想去台北文青的地方",  # 選填
    line_id="user123"         # 選填,用於儲存紀錄
    )

# 印出行程
controller.trip_planner.print_itinerary(result)
```

### 使用包裝好的函式
如果想要更簡單的使用方式，可以直接使用 `run_trip_planner` 函式：

```python
from main import run_trip_planner

# 首次規劃
result = run_trip_planner(
    text="想去台北文青的地方",  # 選填
    line_id="user123"         # 選填,用於儲存紀錄
)

# 重新規劃 - 系統會考慮之前的輸入紀錄
new_result = run_trip_planner(
    line_id="user123"
)
```

## Setup

### 環境變數設定
在 `.env` 檔案中設置以下變數：
```env
jina_url=xxx
jina_headers_Authorization=xxx 
qdrant_url=xxx
qdrant_api_key=xxx
ChatGPT_api_key=xxx
GOOGLE_MAPS_API_KEY=xxx
MONGODB_URI=xxx
```

## Output
```python
[{
    "step": 0,            # 順序編號
    "name": "地點名稱",
    "label": "景點類型",  # 景點/餐廳/起點/終點
    "period": "morning",  # 時段標記
    "lat": 25.0478,      # 緯度
    "lon": 121.5170,     # 經度
    "start_time": "09:00",# 到達時間 
    "end_time": "10:00",  # 離開時間
    "hours": {           # 營業時間
        "start": "09:00",
        "end": "21:00"  
    },
    "duration": 60,      # 停留時間(分鐘)
    "transport": {       # 交通資訊
        "mode": "開車",  # 交通方式
        "time": 15,      # 所需時間(分鐘)
        "travel_distance": 2.5, # 距離(公里)
        "period": "08:45-09:00" # 交通時段
    },
    "route_info": {},   # 路線資訊
    "route_url": "",    # Google Maps連結
}]
```
