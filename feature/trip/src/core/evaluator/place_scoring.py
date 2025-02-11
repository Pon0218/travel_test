# src/core/evaluator/place_scoring.py

from datetime import datetime
from typing import Dict, Optional
from dataclasses import dataclass
from ..models.place import PlaceDetail
from ..services.time_service import TimeService
from ..services.geo_service import GeoService


@dataclass
class ScoreWeights:
    """評分權重設定

    這個類別用來定義各個評分因素的權重，讓評分系統更有彈性。
    所有權重值應介於 0-1 之間，且總和為 1。
    """
    rating_weight: float = 0.3       # 基礎評分權重
    efficiency_weight: float = 0.3   # 時間效率權重
    time_slot_weight: float = 0.2    # 時段適合度權重
    distance_weight: float = 0.2     # 距離合理性權重


class PlaceScoring:
    """地點評分系統

    這個系統負責計算每個地點的基礎評分，考慮：
    1. 地點本身的評分（rating）- 反映基本品質
    2. 營業時間限制 - 確保地點可訪問
    3. 時間效率 - 評估交通與停留時間的合理性
    4. 時段適合度 - 判斷是否在合適的時間前往
    """

    # 分數正規化範圍
    MIN_SCORE = 0.0
    MAX_SCORE = 1.0

    # 新增不同交通方式的距離門檻(公里)
    DISTANCE_THRESHOLDS = {
        'driving': 30,
        'transit': 10,
        'walking': 2,
        'bicycling': 5
    }

    # 效率評分的基準值
    EFFICIENCY_BASE = 1.5  # 基準效率比率
    EFFICIENCY_RATIOS = {
        '景點': 0.8,    # 景點可接受較低效率
        '主要景點': 0.8,
        '餐廳': 1.2,    # 餐廳要求較高效率
        '小吃': 1.2
    }

    def __init__(
        self,
        time_service:             TimeService,
        geo_service: GeoService,
        travel_mode: str = 'driving',
        weights: ScoreWeights = None
    ):
        """初始化評分系統

        Args:
            time_service: TimeService - 時間服務
            geo_service: GeoService - 地理服務 
            travel_mode: str - 交通方式
            weights: ScoreWeights - 評分權重(選填)
        """
        self.time_service = time_service
        self.geo_service = geo_service
        self.travel_mode = travel_mode
        self.weights = weights or ScoreWeights()

        # 設定距離門檻
        self.distance_threshold = self.DISTANCE_THRESHOLDS.get(
            travel_mode,
            self.DISTANCE_THRESHOLDS['driving']
        )

    def calculate_score(
        self,
        place: PlaceDetail,
        current_location: PlaceDetail,
        current_time: datetime,
        travel_time: float
    ) -> float:
        """計算地點的綜合評分

        Args:
            place: PlaceDetail - 要評分的地點
            current_location: PlaceDetail - 當前位置 
            current_time: datetime - 當前時間
            travel_time: float - 預估交通時間(分鐘)

        Returns:
            float: 評分結果,營業時間無效時返回負無限大
        """
        # 檢查營業時間
        if not self._check_business_hours(place, current_time):
            return float('-inf')

        # 計算距離
        distance = self.geo_service.calculate_distance(
            {'lat': current_location.lat, 'lon': current_location.lon},
            {'lat': place.lat, 'lon': place.lon}
        )

        # 調整距離門檻
        adjusted_threshold = self.distance_threshold
        if place.label in ['景點', '主要景點']:
            adjusted_threshold *= 1.2
        elif place.label in ['餐廳', '小吃']:
            adjusted_threshold *= 0.8

        # 計算距離分數
        if distance <= adjusted_threshold:
            # 在門檻內,線性計算分數
            distance_score = 1.0 - (distance / adjusted_threshold)
        else:
            # 超過門檻,快速遞減分數
            over_ratio = (distance - adjusted_threshold) / adjusted_threshold
            distance_score = max(0.0, 0.5 - over_ratio)

        # 計算其他維度分數
        rating_score = self._calculate_rating_score(place)
        efficiency_score = self._calculate_efficiency_score(place, travel_time)
        time_slot_score = self._calculate_time_slot_score(place, current_time)

        # 計算加權平均
        weighted_score = (
            rating_score * self.weights.rating_weight +
            efficiency_score * self.weights.efficiency_weight +
            time_slot_score * self.weights.time_slot_weight +
            distance_score * self.weights.distance_weight
        )

        return self._normalize_score(weighted_score)

    def _calculate_rating_score(self, place: PlaceDetail) -> float:
        """計算基礎評分分數

        這個方法把地點原始的評分（通常是0-5分）轉換成標準化的0-1分數。
        考慮了幾種特殊情況：
        - 若評分特別高（4.5以上），給予額外加分來鼓勵選擇高品質景點
        - 若沒有評分資料，給予中等分數避免完全排除該地點
        - 線性轉換確保分數分布合理

        Args:
            place: 要評分的地點

        Returns:
            float: 0-1 之間的標準化評分
        """
        if not place.rating:
            return 0.5  # 無評分時給予中等分數

        # 基本分數：將 0-5 分轉換為 0-1 分
        base_score = min(1.0, place.rating / 5.0)

        # 高評分獎勵機制（4.5分以上的地點）
        if place.rating >= 4.5:
            bonus = (place.rating - 4.5) * 0.1  # 最多加 0.05 分
            return min(1.0, base_score + bonus)

        return base_score

    def _calculate_efficiency_score(self, place: PlaceDetail, travel_time: float) -> float:
        """計算時間效率分數

        評估到達地點的時間成本與停留價值的比例。這個評分機制：
        - 平衡了交通時間和停留時間的關係
        - 對不同類型的地點有不同的期望值（如景點可以接受較長的交通時間）
        - 確保時間投入有合理的回報

        Args:
            place: PlaceDetail - 要評分的地點
            travel_time: float - 預估交通時間(分鐘)

        Returns:
            float: 0-1之間的效率分數
        """
        if travel_time <= 0:
            return 1.0  # 如果就在當前位置，給予最高分

        # 計算效率比率（停留時間/交通時間）
        efficiency_ratio = place.duration_min / travel_time

        # 根據地點類型調整期望效率
        expected_ratio = self.EFFICIENCY_BASE * \
            self.EFFICIENCY_RATIOS.get(place.label, 1.0)

        # 標準化評分
        score = min(1.0, efficiency_ratio / expected_ratio)
        return max(0.0, score)

    # def _calculate_distance_score(
    #     self,
    #     place: PlaceDetail,
    #     current_location: PlaceDetail,
    #     travel_mode: str = 'driving'
    # ) -> float:
    #     """計算距離合理性分數

    #     根據交通方式調整評分:
    #     1. 計算實際距離
    #     2. 取得對應交通方式的門檻
    #     3. 根據距離比例計算分數

    #     Args:
    #         place: PlaceDetail - 要評分的地點
    #         current_location: PlaceDetail - 當前位置
    #         travel_mode: str - 交通方式

    #     Returns:
    #         float: 0-1之間的距離分數,距離越近分數越高
    #     """
    #     # 計算實際距離
    #     distance = self.geo_service.calculate_distance(
    #         {'lat': current_location.lat, 'lon': current_location.lon},
    #         {'lat': place.lat, 'lon': place.lon}
    #     )

    #     # 取得該交通方式的距離門檻
    #     threshold = self.DISTANCE_THRESHOLDS.get(
    #         travel_mode,
    #         self.DISTANCE_THRESHOLDS['driving']
    #     )

    #     # 根據地點類型調整可接受距離
    #     if place.label in ['景點', '主要景點']:
    #         threshold *= 1.2  # 景點可以接受較遠的距離
    #     elif place.label in ['餐廳', '小吃']:
    #         threshold *= 0.8  # 餐飲地點要求較近

    #     # 計算距離分數（線性遞減）
    #     if distance <= threshold:
    #         # 在門檻內,線性計算分數
    #         score = 1.0 - (distance / threshold)
    #     else:
    #         # 超過門檻,快速遞減分數
    #         over_ratio = (distance - threshold) / threshold
    #         score = max(0.0, 0.5 - over_ratio)  # 超過門檻越多分數越低

    #     return max(0.0, min(1.0, score))

    def _calculate_time_slot_score(self, place: PlaceDetail, current_time: datetime) -> float:
        """計算時段適合度分數

        評估當前時間是否適合造訪該地點。這個評分機制考慮：
        - 是否在建議的遊玩時段
        - 與建議時段的時間差距
        - 營業時間的剩餘時間

        Args:
            place: 要評分的地點
            current_time: 當前時間

        Returns:
            float: 0-1 之間的時段適合度分數
        """
        # 取得當前時段
        current_period = self.time_service.get_time_period(current_time)

        # 基本分數：是否在建議時段
        if current_period == place.period:
            base_score = 1.0
        else:
            # 不在建議時段，根據時段差距給予部分分數
            periods = ['morning', 'lunch', 'afternoon', 'dinner', 'night']
            current_idx = periods.index(current_period)
            place_idx = periods.index(place.period)
            period_diff = abs(current_idx - place_idx)

            base_score = max(0.3, 1.0 - (period_diff * 0.2))

        # 考慮營業時間的影響
        hours_score = self._evaluate_business_hours_fit(place, current_time)

        return min(1.0, base_score * hours_score)

    def _check_business_hours(self, place: PlaceDetail, current_time: datetime) -> bool:
        """檢查地點是否在營業時間內

        使用地點的營業時間資訊來判斷當前是否營業。

        Args:
            place: 要檢查的地點
            current_time: 要檢查的時間

        Returns:
            bool: True 表示營業中,False 表示不營業
        """
        weekday = current_time.isoweekday()  # 1-7 代表週一到週日
        time_str = current_time.strftime(self.time_service.TIME_FORMAT)

        # 檢查hours是否存在且有效
        if not place.hours or weekday not in place.hours:
            return False

        # 檢查該天的營業時段
        slots = place.hours[weekday]
        if not slots or not isinstance(slots, list):
            return False

        # 使用place的is_open_at方法檢查營業狀態
        return place.is_open_at(weekday, time_str)

    def _evaluate_business_hours_fit(
        self,
        place: PlaceDetail,
        current_time: datetime
    ) -> float:
        """評估營業時間的適合度

        不僅檢查地點是否營業，還評估：
        - 距離打烊時間還有多久（避免太接近打烊時間）
        - 是否有足夠的遊玩時間
        - 當前是否處於營業的黃金時段

        Args:
            place: 要評分的地點
            current_time: 當前時間

        Returns:
            float: 0-1 之間的適合度分數
        """
        weekday = current_time.isoweekday()
        time_str = current_time.strftime(self.time_service.TIME_FORMAT)

        # 先檢查是否營業
        if not self._check_business_hours(place, current_time):
            return 0.0

        # 檢查剩餘營業時間
        slots = place.hours.get(weekday, [])
        if not slots or not isinstance(slots, list):
            return 0.0

        best_score = 0.0  # 取多個時段中的最佳分數

        for slot in slots:
            if not slot or not isinstance(slot, dict):
                continue

            current_slot_score = self._calculate_slot_score(
                current_time,
                slot,
                place.duration_min
            )
            best_score = max(best_score, current_slot_score)

        return best_score

    def _calculate_slot_score(
        self,
        current_time: datetime,
        slot: Dict[str, str],
        duration_min: int
    ) -> float:
        """計算單一時段的適合度分數

        Args:
            current_time: 當前時間
            slot: 營業時段資訊
            duration_min: 預計停留時間

        Returns:
            float: 0-1 之間的分數
        """
        # 解析結束時間
        closing_time = datetime.strptime(slot['end'],
                                         self.time_service.TIME_FORMAT).time()
        current_minutes = current_time.hour * 60 + current_time.minute
        closing_minutes = closing_time.hour * 60 + closing_time.minute

        # 如果是跨日營業，調整結束時間
        if closing_time < datetime.strptime(slot['start'],
                                            self.time_service.TIME_FORMAT).time():
            closing_minutes += 24 * 60

        # 計算剩餘時間
        remaining_minutes = closing_minutes - current_minutes
        if remaining_minutes < 0:
            remaining_minutes += 24 * 60

        # 根據剩餘時間評分
        if remaining_minutes < duration_min:
            return 0.0  # 剩餘時間不足
        elif remaining_minutes < duration_min * 1.5:
            return 0.5  # 時間稍嫌緊湊
        else:
            return 1.0  # 有充足時間

    def _normalize_score(self, score: float) -> float:
        """標準化評分到合理範圍

        Args:
            score: float - 原始評分

        Returns:
            float: 標準化後的評分(0-1之間)
        """
        return max(self.MIN_SCORE, min(self.MAX_SCORE, score))
