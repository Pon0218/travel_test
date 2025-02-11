# src/core/planner/strategy.py

from datetime import datetime, timedelta
from math import ceil
import random
from typing import List, Dict, Optional, Tuple
from zoneinfo import ZoneInfo

from ..models.place import PlaceDetail
from ..services.time_service import TimeService
from ..services.geo_service import GeoService
from ..evaluator.place_scoring import PlaceScoring


class BasePlanningStrategy:
    """行程規劃策略基礎類別

    此類別負責:
    1. 管理時段狀態與轉換
    2. 選擇適合的下一個地點
    3. 建立完整行程規劃
    4. 追蹤規劃進度
    """

    def __init__(
        self,
        time_service: TimeService,
        geo_service: GeoService,
        place_scoring: PlaceScoring,
        config: Dict
    ):
        """初始化

        Args:
            time_service: 時間服務
            geo_service: 地理服務 
            place_scoring: 地點評分服務
            config: 規劃設定,必須包含:
                - start_time: datetime 
                - end_time: datetime 
                - travel_mode: str
        """
        # 基礎服務元件
        self.time_service = time_service
        self.geo_service = geo_service
        self.place_scoring = PlaceScoring(
            time_service=time_service,
            geo_service=geo_service,
            travel_mode=config['travel_mode']  # 傳入交通方式
        )
        self.config = config

        # 基本設定
        self.start_time = config['start_time']
        self.end_time = config['end_time']
        self.travel_mode = config['travel_mode']
        self.distance_threshold = config.get('distance_threshold', 30)
        self.end_location = config.get('end_location')

        # 時段管理
        self.period_sequence = [
            'morning', 'lunch', 'afternoon', 'dinner', 'night'
        ]
        self.period_status = {period: False for period in self.period_sequence}
        self.current_period = 'morning'

        # 狀態追蹤
        self.visited_places = set()  # 使用set避免重複選擇地點
        self._itinerary = []  # 儲存規劃的行程
        self.total_distance = 0.0  # 總行程距離

        # 用餐狀態
        self.lunch_completed = False
        self.dinner_completed = False

    def select_next_place(
        self,
        current_location: PlaceDetail,
        available_places: List[PlaceDetail],
        current_time: datetime,
        trip_date: datetime,
    ) -> Optional[Tuple[PlaceDetail, Dict]]:
        """選擇下一個地點

        Args:
            current_location: 當前位置
            available_places: 可選擇的地點列表
            current_time: 當前時間

        Returns:
            Optional[Tuple[PlaceDetail, Dict]]: 選中的地點和交通資訊,
                                            若無合適地點則返回None
        """
        # 1. 取得當前時段
        current_period = self.time_service.get_current_period(current_time)

        # 2. 篩選符合時段且有效的地點
        suitable_places = []

        for place in available_places:
            # 檢查基本條件
            if (place.period != current_period or
                    place.name in self.visited_places):
                continue

            # 檢查營業時間
            weekday = trip_date.isoweekday()
            time_str = current_time.strftime(TimeService.TIME_FORMAT)
            if not place.is_open_at(weekday, time_str):
                continue

            suitable_places.append(place)

        if not suitable_places:
            print(f"沒有符合{current_period}時段的地點")
            return None

        # 3. 計算直線距離並評分
        scored_places = []
        for place in suitable_places:
            distance = self.geo_service.calculate_distance(
                {'lat': current_location.lat, 'lon': current_location.lon},
                {'lat': place.lat, 'lon': place.lon}
            )

            estimated_time = distance * 2
            score = self.place_scoring.calculate_score(
                place=place,
                current_location=current_location,
                current_time=current_time,
                travel_time=estimated_time
            )
            if score > float('-inf'):
                scored_places.append((place, score))

        if not scored_places:
            print("沒有在可接受距離內的地點")
            return None

        # 4. 取評分最高的前3-5個地點
        top_places = sorted(
            scored_places,
            key=lambda x: x[1],
            reverse=True
        )[:5]

        # 5. 隨機選擇一個
        selected_place, _ = random.choice(
            top_places[:max(3, len(top_places))]
        )

        # 6. 只對選中的地點取得路線資訊
        travel_info = self.geo_service.get_route(
            origin={"lat": current_location.lat, "lon": current_location.lon},
            destination={"lat": selected_place.lat, "lon": selected_place.lon},
            mode=self.travel_mode,
            departure_time=current_time
        )

        # 7. 更新用餐狀態
        self.time_service.update_meal_status(selected_place.period)

        return selected_place, travel_info

    def execute(
        self,
        current_location: PlaceDetail,
        available_places: List[PlaceDetail],
        current_time: datetime,
        previous_trip: List[Dict] = None,
        requirement: List[Dict] = None,
    ) -> List[Dict]:
        """執行行程規劃

        這是策略的主要執行方法,負責:
        1. 初始化行程狀態
        2. 依照時段選擇適合的地點
        3. 建立完整行程資訊
        4. 追蹤時段和用餐狀態

        Args:
            current_location: PlaceDetail - 起點位置
            available_places: List[PlaceDetail] - 所有可選擇的地點
            current_time: datetime - 開始時間
            previous_trip: 之前的行程(選填)

        Returns:
            List[Dict] - 完整的行程列表,每個行程項目包含:
                - name: str - 地點名稱
                - step: int - 順序編號
                - start_time: str - 到達時間(HH:MM格式)
                - end_time: str - 離開時間(HH:MM格式)
                - duration: int - 停留時間(分鐘)
                - travel_time: int - 交通時間(分鐘)
                - travel_distance: float - 交通距離(公里)
                - transport: str - 交通方式
                - route_info: Dict - 路線資訊(如果有)
        """
        # 初始化行程
        if not hasattr(self, '_itinerary'):
            self._itinerary = []
        else:
            self._itinerary.clear()

        # 重置時間服務狀態
        self.time_service.reset()
        self.visited_places.clear()

        if requirement and requirement.get('date'):
            current_year = datetime.now(ZoneInfo('Asia/Taipei')).year
            trip_date = f"{current_year}-{requirement['date']}"
            trip_date = datetime.strptime(trip_date, "%Y-%m-%d").replace(
                tzinfo=ZoneInfo('Asia/Taipei')
            )
        else:
            trip_date = datetime.now(
                ZoneInfo('Asia/Taipei')) + timedelta(days=1)

        original_start = None

        # 如果有之前的行程 先加入
        if previous_trip:
            self._itinerary.extend(previous_trip)
            # 把之前的地點加入已訪問集合
            self.visited_places.update(item['name'] for item in previous_trip)

            # 檢查並設定時段狀態
            for item in previous_trip:
                if item['period'] == 'lunch':
                    self.time_service.lunch_completed = True
                    self.time_service.current_period = 'afternoon'
                elif item['period'] == 'dinner':
                    self.time_service.lunch_completed = True
                    self.time_service.current_period = 'night'

                if item['step'] == 0:
                    original_start = item

        # 設定終點
        if requirement and requirement.get('end_point'):
            self.end_location = self.geo_service.geocode(requirement.get('end_point'))
            self.end_location = PlaceDetail(**self.end_location)
        elif original_start:
            # 如果有原始行程,用原始起點作為終點
            self.end_location = self._convert_to_place_detail(original_start)

        # 加入起點(如果不是繼續規劃)
        if not previous_trip:
            start_item = self._create_itinerary_item(
                place=current_location,
                arrival_time=current_time,
                departure_time=current_time,  # 起點不需要停留時間
                travel_info={
                    'duration_minutes': 0,
                    'distance_km': 0,
                    'transport_mode': self.travel_mode
                },
                trip_date=trip_date
            )
            self.visited_places.add(current_location.name)
            self._itinerary.append(start_item)

        print(f"\n=== 開始規劃行程 ===")

        # 初始化規劃狀態
        remaining_places = available_places.copy()
        current_loc = current_location
        visit_time = current_time
        iteration = 1

        # 主要規劃迴圈
        while remaining_places and visit_time < self.end_time:
            # 選擇下一個地點
            next_place = self.select_next_place(
                current_loc,
                remaining_places,
                visit_time,
                trip_date
            )

            if not next_place:
                print("找不到合適的下一個地點,結束規劃")
                break

            place, travel_info = next_place

            # 計算到達和離開時間
            arrival_time = self._calculate_arrival_time(
                visit_time,
                travel_info['duration_minutes']
            )
            departure_time = self._calculate_departure_time(
                arrival_time,
                place.duration_min
            )

            # 預估返回終點所需時間
            to_home_info = self.geo_service.get_route(
                origin={"lat": place.lat, "lon": place.lon},
                destination={
                    "lat": self.end_location.lat,
                    "lon": self.end_location.lon
                },
                mode=self.travel_mode,
                departure_time=departure_time
            )
            print(self.end_location)
            print(1)

            final_time = self._calculate_arrival_time(
                departure_time,
                to_home_info['duration_minutes']
            )

            # 檢查是否超過結束時間
            if final_time > self.end_time:
                print("加入此地點後會超過結束時間,直接返回終點")
                break

            # 建立行程項目
            itinerary_item = self._create_itinerary_item(
                place,
                arrival_time,
                departure_time,
                travel_info,
                trip_date
            )
            self._itinerary.append(itinerary_item)

            # 更新規劃狀態
            current_loc = place
            visit_time = departure_time
            remaining_places.remove(place)
            self.visited_places.add(place.name)
            self.total_distance += travel_info['distance_km']

            iteration += 1

        # 加入返回終點
        if self._itinerary[-1]['name'] != self.end_location.name:  # 使用設定的終點
            # 計算返回終點的路線
            final_travel_info = self.geo_service.get_route(
                origin={
                    "lat": float(self._itinerary[-1]['lat']),
                    "lon": float(self._itinerary[-1]['lon'])
                },
                destination={
                    "lat": self.end_location.lat,  # 使用設定的終點
                    "lon": self.end_location.lon
                },
                mode=self.travel_mode
            )

            final_arrival_time = self._calculate_arrival_time(
                visit_time,
                final_travel_info['duration_minutes']
            )

            # 根據實際抵達時間更新終點的period
            self.end_location.period = self.time_service.get_time_period(
                final_arrival_time
            )

            # 加入終點到行程
            end_item = self._create_itinerary_item(
                place=self.end_location,  # 使用設定的終點
                arrival_time=final_arrival_time,
                departure_time=final_arrival_time,
                travel_info=final_travel_info,
                trip_date=trip_date
            )
            self._itinerary.append(end_item)
            self.total_distance += final_travel_info['distance_km']

        print(f"\n=== 行程規劃完成 ===")
        print(f"規劃地點數: {len(self._itinerary)}")
        print(f"總行程距離: {self.total_distance:.0f} 公里")

        return self._itinerary

    def _calculate_arrival_time(self,
                                start_time: datetime,
                                travel_minutes: float) -> datetime:
        """計算到達時間

        根據出發時間和交通時間計算預計到達時間

        Args:
            start_time: datetime 出發時間
            travel_minutes: float 交通時間(分鐘)

        Returns:
            datetime 預計到達時間
        """
        return start_time + timedelta(minutes=int(travel_minutes))

    def _calculate_departure_time(self,
                                  arrival_time: datetime,
                                  duration_minutes: int) -> datetime:
        """計算離開時間

        根據到達時間和停留時間計算預計離開時間

        Args:
            arrival_time: datetime 到達時間
            duration_minutes: int 停留時間(分鐘)

        Returns:
            datetime 預計離開時間
        """
        return arrival_time + timedelta(minutes=duration_minutes)

    def _create_itinerary_item(
        self,
        place: PlaceDetail,
        arrival_time: datetime,
        departure_time: datetime,
        travel_info: Dict,
        trip_date: datetime = None,  # YYYY-MM-DD
    ) -> Dict:
        """建立行程項目

        整合地點、時間和交通等資訊,建立完整的行程項目資料。

        Args:
            place: PlaceDetail - 地點資訊
            arrival_time: datetime - 到達時間 
            departure_time: datetime - 離開時間
            travel_info: Dict - 交通資訊,應包含:
                - duration_minutes: int 
                - distance_km: float
                - transport_mode: str
                - route_info: Dict (選填)

        Returns:
            Dict: 包含以下資訊的行程項目:
                - name: str
                - label: str  
                - hours: str
                - lat/lon: float
                - start_time/end_time: str (HH:MM格式)
                - duration: int (分鐘)
                - transport: Dict
                - period: str
        """
        # 如果沒有傳入日期 預設明天
        if not trip_date:
            trip_date = datetime.now(
                ZoneInfo('Asia/Taipei')) + timedelta(days=1)

        # 將抵達時間四捨五入到最近的5分鐘
        rounded_minutes = ceil(arrival_time.minute / 5) * 5

        if rounded_minutes == 60:
            rounded_arrival = arrival_time.replace(
                hour=arrival_time.hour + 1, minute=0)
        else:
            rounded_arrival = arrival_time.replace(minute=rounded_minutes)

        # 調整離開時間,保持相同的停留時間
        time_diff = rounded_arrival - arrival_time
        rounded_departure = departure_time + time_diff

        # 取得當天的營業時間
        weekday = trip_date.isoweekday()
        day_hours = place.hours.get(weekday, [])

        # 找出符合抵達時間的營業時段
        matching_hours = None
        for slot in day_hours:
            if not slot:
                continue
            start = datetime.strptime(slot['start'], '%H:%M').time()
            end = datetime.strptime(slot['end'], '%H:%M').time()

            # 一般情況或跨日檢查
            if end < start:  # 跨日營業
                if arrival_time.time() >= start or arrival_time.time() <= end:
                    matching_hours = slot
                    break
            else:  # 一般情況
                if start <= arrival_time.time() <= end:
                    matching_hours = slot
                    break

        # 計算交通時段
        travel_end = arrival_time
        travel_start = travel_end - \
            timedelta(minutes=travel_info.get('duration_minutes', 0))
        travel_period = (
            f"{travel_start.strftime('%H:%M')}-"
            f"{travel_end.strftime('%H:%M')}"
        )

        # 把起點終點的label替換
        if len(self.visited_places) == 0:
            display_label = '起點'
        elif self.end_location and place.name == self.end_location.name:
            display_label = '終點'
        else:
            display_label = place.label

        # 交通方式中英對照
        transport_display = {
            'transit': '大眾運輸',
            'driving': '開車',
            'walking': '步行',
            'bicycling': '騎車'
        }
        transport_mode = travel_info.get('transport_mode', self.travel_mode)
        transport_chinese = transport_display.get(
            transport_mode,
            # transport_mode,
        )

        return {
            'step': len(self.visited_places),
            'place_id': place.place_id,
            'name': place.name,
            'label': display_label,
            'hours': matching_hours,
            'lat': place.lat,
            'lon': place.lon,
            'date': trip_date.strftime("%Y-%m-%d"),
            'start_time': rounded_arrival.strftime('%H:%M'),
            'end_time': rounded_departure.strftime('%H:%M'),
            'duration': place.duration_min,
            'transport': {
                'mode': transport_chinese,
                'mode_eng': transport_mode,
                'travel_distance': travel_info.get('distance_km', 0),
                'time': travel_info.get('duration_minutes', 20),
                'period': travel_period,
            },
            'route_info': travel_info.get('route_info'),
            'route_url': place.url,
            'period': place.period,
        }

    def _convert_to_place_detail(self, item: Dict) -> PlaceDetail:
        """將行程項目轉換為PlaceDetail物件"""
        return PlaceDetail(
            name=item['name'],
            lat=item['lat'],
            lon=item['lon'],
            duration_min=0,
            label='交通樞紐',
            period='night',
            hours={i: [{'start': '00:00', 'end': '23:59'}]
                   for i in range(1, 8)}
        )
