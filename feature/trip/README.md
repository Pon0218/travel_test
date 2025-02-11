# 改良貪婪演算法

針對一日行程規劃的改良貪婪演算法,強調時段、距離、效率綜合考量。

## 使用方式
```python
from feature.trip import TripPlanningSystem

# 執行規劃
result = TripPlanningSystem().plan_trip(
   locations=[{
       'name': '地點名稱',
       'rating': 4.5,
       'lat': 25.0478,
       'lon': 121.5170,
       'duration': 60,     # 停留時間(分鐘)
       'label': '景點',    # 景點/餐廳
       'period': 'morning',# 時段標記
       'hours': {         # 營業時間
           1: [{'start':'09:00', 'end':'22:00'}]
       }
   }],
   requirement={
       'start_time': '09:00',
       'end_time': '21:00',
       'transport_mode': 'driving',   # driving/transit/walking
       'distance_threshold': 30       # 最大距離(公里)  
   },
   previous_trip=[],       # 選填:之前規劃的行程
   restart_index=None      # 選填:從哪個點重新規劃
)
```

## 演算法流程
### 1. 資料準備
- 建立時段池(morning/lunch/afternoon/dinner/night)
- 初始化可用地點列表
- 設定起點與時間限制

### 2. 選點評估
- 每次選擇下一個地點時:
    #### a. 時段篩選
    - 依據當前時間判斷時段
    - 只從對應時段的地點池中選擇
    - 用餐時段強制選擇餐廳

    #### b. 基礎過濾
    - 檢查營業時間
    - 驗證距離限制(預設30公里內)
    - 排除已訪問的地點

    #### c. 綜合評分機制
    - 基本評分: 地點評分(4.5分以上加成) × 0.3
    - 效率評分: 停留時間/交通時間(依地點類型調整) × 0.3
    - 時段適配: 營業時間充足度 × 0.2
    - 距離評分: 依地點類型調整可接受範圍 × 0.2

### 3. 決策機制

- 計算每個地點的綜合分數
- 篩選出分數高於門檻的候選點
- 取評分最高前5名
- 隨機選擇一個地點
- 取得Google Maps實際路線資訊

### 4. 時段轉換
#### 固定順序:
morning → lunch → afternoon → dinner → night
#### 轉換條件:

- morning到lunch: 到達午餐時間
- lunch到afternoon: 完成午餐
- afternoon到dinner: 到達晚餐時間
- dinner到night: 完成晚餐

### 5. 結束條件

- 達到結束時間
- 所有時段完成
- 找不到合適的下一個地點

## 核心特點

- 彈性的時段管理
- 多維度的評分機制
- 隨機性避免路線過於制式
- 整合實際交通資訊
  