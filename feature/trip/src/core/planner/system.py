# src/core/planner/system.py


from datetime import datetime, timedelta
from typing import Dict, List
from ..evaluator.place_scoring import PlaceScoring
from ..models.place import PlaceDetail
from .strategy import BasePlanningStrategy
from ..services.geo_service import GeoService
from ..services.time_service import TimeService
from ..utils.navigation_translator import NavigationTranslator


class TripPlanningSystem:
    """行程規劃系統

    整合各種服務來規劃最佳行程:
    1. 時間管理：使用 TimeService 處理時段和時間
    2. 地理服務：計算距離和規劃路線
    3. 評分服務：評估地點適合度
    4. 策略系統：執行實際的規劃邏輯
    """

    def __init__(self):
        """初始化規劃系統並連結所有需要的服務"""
        # 初始化時間服務，設定預設用餐時間
        self.time_service = TimeService(
            lunch_time="12:00",   # 預設中午12點用餐
            dinner_time="18:00"   # 預設晚上6點用餐
        )

        # 初始化其他服務
        self.geo_service = GeoService()
        self.place_scoring = PlaceScoring(
            time_service=self.time_service,
            geo_service=self.geo_service
        )

        # 初始化策略系統
        self.strategy = None

        # 初始化時間相關屬性
        self.start_time = None
        self.end_time = None

        # 執行狀態追蹤
        self.execution_time = 0.0

    def plan_trip(
        self,
        locations: List[Dict],
        requirement: Dict,
        previous_trip: List[Dict] = None,
        restart_index: int = None
    ) -> List[Dict]:
        """執行行程規劃

        Args:
            locations: 可用的景點列表
            requirement: 規劃需求
            previous_trip: 之前規劃的行程(選填)
            restart_index: 從哪個點重新開始(選填)

        Returns:
            List[Dict]: 規劃好的行程列表
        """
        start_time = datetime.now()

        try:
            # 把 requirement 的 key 中文改成英文
            requirement = self._convert_keys(requirement)

            # 如果要從中間開始規劃
            if (previous_trip and
                restart_index is not None and
                restart_index > 0 and
                    restart_index <= len(previous_trip)):

                # 取得之前行程的最後一個點
                restart_point = previous_trip[restart_index-1]
                # 修改開始時間
                requirement['start_time'] = restart_point['end_time']
                requirement['start_point'] = restart_point['name']

            requirement = self._set_defaults(requirement)

            # 設定時間屬性
            self.start_time = datetime.strptime(
                requirement['start_time'], '%H:%M'
            )
            self.end_time = datetime.strptime(
                requirement['end_time'], '%H:%M'
            )

            # 設定起點和終點
            self.start_location = self._get_start_location(
                requirement.get('start_point')
            )
            self.end_location = self._get_end_location(
                requirement.get('end_point')
            )

            # 更新時間服務的用餐時間設定
            if requirement.get('lunch_time'):
                self.time_service = TimeService(
                    lunch_time=requirement['lunch_time'],
                    dinner_time=requirement.get('dinner_time', "18:00")
                )

            # 轉換地點資料為 PlaceDetail 物件
            available_places = [
                PlaceDetail(**location) if isinstance(location, dict)
                else location for location in locations
            ]

            # 準備規劃上下文
            context = {
                'start_time': self.start_time,
                'end_time': self.end_time,
                'travel_mode': requirement.get('transport_mode', 'driving'),
                'distance_threshold': requirement.get('distance_threshold', 30),
                'start_location': self.start_location,
                'end_location': self.end_location,
            }

            # 初始化並執行規劃策略
            self.strategy = BasePlanningStrategy(
                time_service=self.time_service,
                geo_service=self.geo_service,
                place_scoring=self.place_scoring,
                config=context
            )

            # 執行規劃
            itinerary = self.strategy.execute(
                current_location=self.start_location,
                available_places=available_places,
                current_time=context['start_time'],
                previous_trip=previous_trip[:restart_index] if previous_trip else None,
                requirement=requirement
            )

            # 記錄執行時間
            self.execution_time = (datetime.now() - start_time).total_seconds()

            return itinerary

        except Exception as e:
            print(f"行程規劃失敗: {str(e)}")
            raise


    def print_itinerary(self, itinerary: List[Dict], show_navigation: bool = False) -> None:
        """輸出行程規劃結果

        Args:
            itinerary: List[Dict] - 規劃好的行程列表
            show_navigation: bool - 是否顯示詳細導航資訊
        """
        print("\n=== 行程規劃結果 ===")

        total_travel_time = 0
        total_duration = 0

        for plan in itinerary:
            # 顯示地點資訊
            print(f"\n[地點 {plan['step']}] "
                  f"Period: {plan['period']}")
            print(f"名稱: {plan['name']},"
                  f" Label: {plan['label']},"
                  f" 營業時間: {plan['hours']}")
            print(f"時間: {plan['start_time']} - {plan['end_time']}")
            print(f"停留: {plan['duration']}分鐘", end=' ')
            print(f"交通: {plan['transport']['mode']}"
                  f"({plan['transport']['time']}分鐘)")

            # 如果需要，顯示詳細導航
            if show_navigation and 'route_info' in plan:
                print("\n前往下一站的導航:")
                print(NavigationTranslator.format_navigation(
                    plan['route_info']))

            total_travel_time += plan['transport']['time']
            total_duration += plan['duration']

        # 顯示統計資訊
        print("\n=== 統計資訊 ===")
        print(f"總景點數: {len(itinerary)}個")
        print(f"總時間: {(total_duration + total_travel_time)/60:.1f}小時")
        print(f"- 遊玩時間: {total_duration/60:.1f}小時")
        print(f"- 交通時間: {total_travel_time/60:.1f}小時")

        print(f"規劃耗時: {self.execution_time:.2f}秒")

    def _get_start_location(self, start_point: str) -> PlaceDetail:
        """處理起點設定

        將起點資訊轉換為 PlaceDetail 物件

        Args:
            start_point: str - 起點的名稱

        Returns:
            PlaceDetail - 起點的完整資訊物件
        """
        # 準備預設的起點資料
        default_location = {
            'name': '台北車站',
            'lat': 25.0478,
            'lon': 121.5170,
            'duration_min': 0,
            'label': '交通樞紐',
            'period': self.time_service.get_time_period(self.start_time),
            'hours': {
                i: [{'start': '00:00', 'end': '23:59'}] for i in range(1, 8)
            }
        }

        if not start_point or start_point == "台北車站":
            # 使用預設起點
            return PlaceDetail(**default_location)

        try:
            # 如果有指定其他起點，取得該地點資訊
            location = self._get_location_info(start_point)
            # 根據start_time設定period
            location['period'] = self.time_service.get_time_period(
                self.start_time)
            return PlaceDetail(**location)
        except Exception as e:
            print(f"無法取得起點資訊，使用預設起點: {str(e)}")
            return PlaceDetail(**default_location)

    def _get_end_location(self, end_point: str) -> PlaceDetail:
        """取得終點位置資訊

        如果沒有指定終點，會使用起點作為終點
        如果指定了終點，會取得該地點的詳細資訊

        Args:
            end_point: Optional[str] - 終點名稱，可以是 None

        Returns:
            PlaceDetail - 終點的完整資訊物件
        注意:
            - 如果end_point為none,使用起點資料但更新period
            - period為暫時性的,會在execute()時根據實際抵達時間更新
        """
        if not end_point or end_point == "none":
            # 使用起點資料但給予新的period
            end_location = self.start_location.model_copy()
            # 根據end_time設定暫時period (之後會更新)
            end_location.period = self.time_service.get_time_period(
                self.end_time
            )
            return end_location

        try:
            # 如果有指定終點，取得該地點資訊
            location = self._get_location_info(end_point)
            # 設定暫時period
            location['period'] = self.time_service.get_time_period(
                self.end_time)
            return PlaceDetail(**location)
        except Exception as e:
            print(f"無法取得終點資訊，使用起點作為終點: {str(e)}")
            return self.start_location

    def _get_location_info(self, place_name: str) -> Dict:
        """取得地點詳細資訊

        使用地理服務來取得指定地點的完整資訊，包括：
        1. 座標位置
        2. 基本資訊
        3. 營業時間等
        """
        try:
            location = self.geo_service.geocode(place_name)
            return {
                'name': place_name,
                'lat': location['lat'],
                'lon': location['lon'],
                'duration_min': 0,  # 起點/終點不需要停留時間
                'label': '交通樞紐',
                'period': 'morning',  # 起點預設為早上時段
                'hours': {i: [{'start': '00:00', 'end': '23:59'}] for i in range(1, 8)}
            }
        except Exception as e:
            raise ValueError(f"無法取得地點資訊: {str(e)}")

    def _convert_keys(self, requirement: Dict) -> Dict:
        """
        轉換需求字典的中文 key 為英文

        Args:
            requirement: Dict - 使用中文 key 的需求字典
                {
                    "出發時間": "00:00" | "none",
                    "結束時間": "00:00" | "none",
                    ...
                }

        Returns:
            Dict: 使用英文 key 的需求字典
                {
                    "start_time": "00:00" | "none",
                    "end_time": "00:00" | "none",
                    ...
                }
        """
        # 中英文 key 對照表
        KEY_MAPPING = {
            "出發時間": "start_time",
            "結束時間": "end_time",
            "出發地點": "start_point",
            "結束地點": "end_point",
            "交通方式": "transport_mode",
            "可接受距離門檻(KM)": "distance_threshold",
            "早餐時間": "breakfast_time",
            "午餐時間": "lunch_time",
            "晚餐時間": "dinner_time",
            "預算": "budget",
            "出發日": "date"
        }

        # 交通方式對照表
        TRANSPORT_MODE_MAPPING = {
            "大眾運輸": "transit",
            "開車": "driving",
            "騎車": "bicycling",
            "步行": "walking"
        }

        requirement_dict = requirement[0]

        converted = {}
        for zh_key, value in requirement_dict.items():
            if zh_key not in KEY_MAPPING:
                continue

            eng_key = KEY_MAPPING[zh_key]

            # 處理 'none' 轉 None
            if value == 'none':
                value = None

            # 轉換交通方式
            if zh_key == "交通方式" and value in TRANSPORT_MODE_MAPPING:
                value = TRANSPORT_MODE_MAPPING[value]

            converted[eng_key] = value

        return converted

    def _set_defaults(self, requirement: Dict) -> Dict:
        """設定預設值

        Args:
            requirement: 使用者提供的需求字典

        Returns:
            Dict: 包含預設值的完整需求字典
        """
        # 確保時間有值
        start_time = requirement.get('start_time') or "09:00"
        end_time = requirement.get('end_time') or "21:00"

        # 轉換時間格式
        start_dt = datetime.strptime(start_time, '%H:%M')
        end_dt = datetime.strptime(end_time, '%H:%M')

        # 設定午餐時間範圍
        earliest_lunch = datetime.strptime("11:00", '%H:%M')
        latest_lunch = datetime.strptime("13:00", '%H:%M')

        # 計算預設午餐時間
        if end_dt < earliest_lunch:
            # 結束時間在午餐前,不安排午餐
            default_lunch_str = None
        elif start_dt >= latest_lunch:
            # 開始時間太晚,不安排午餐
            default_lunch_str = None
        elif start_dt >= earliest_lunch:
            # 開始時間在11:00-13:00之間,用開始時間後30分鐘
            lunch_dt = start_dt + timedelta(minutes=30)
            if lunch_dt > latest_lunch:
                lunch_dt = latest_lunch
            if lunch_dt > end_dt:
                default_lunch_str = None
            else:
                default_lunch_str = lunch_dt.strftime('%H:%M')
        else:
            # 開始時間夠早,用預設12:00
            default_lunch_str = "12:00"
            if end_dt >= datetime.strptime("12:00", '%H:%M'):
                default_lunch_str = "12:00"
            else:
                default_lunch_str = None

        # 設定晚餐時間
        earliest_dinner = datetime.strptime("16:30", '%H:%M')
        latest_dinner = datetime.strptime("20:00", '%H:%M')

        # 計算預設晚餐時間
        if end_dt <= earliest_dinner:
            # 結束時間比最早晚餐時間還早,不安排晚餐
            default_dinner_str = None
        elif end_dt <= latest_dinner:
            # 結束時間在17:00-19:00之間,用最早晚餐時間
            default_dinner_str = earliest_dinner.strftime('%H:%M')
        elif end_dt >= datetime.strptime("21:30", '%H:%M'):
            # 結束時間較晚,用最晚晚餐時間
            default_dinner_str = latest_dinner.strftime('%H:%M')
        else:
            # 結束時間在19:00-21:00之間,用結束時間-2小時
            dinner_dt = end_dt - timedelta(hours=2)
            default_dinner_str = dinner_dt.strftime('%H:%M')

        # 預設值定義
        default_requirement = {
            "start_time": start_time,
            "end_time": end_time,
            "start_point": "台北車站",
            "end_point": None,
            "transport_mode": "driving",
            "distance_threshold": 30,
            "lunch_time": default_lunch_str,
            "dinner_time": default_dinner_str
        }

        # 更新預設值
        for key, value in requirement.items():
            if value is not None:
                default_requirement[key] = value

        return default_requirement
