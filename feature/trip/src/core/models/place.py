# src/core/models/place.py

from typing import Any, Dict, Optional, Union
import pandas as pd
from pydantic import BaseModel, Field, field_validator, model_validator
from datetime import datetime

from ..services.time_service import TimeService
from ..utils.validator import TripValidator


class PlaceDetail(BaseModel):
    """地點詳細資訊的資料模型

    用於儲存和管理景點、餐廳等地點的完整資訊，包含：
    1. 基本資訊(名稱、位置、評分)
    2. 時間管理(營業時間、建議停留時間)
    3. 分類標籤
    4. 時段標記
    """

    place_id: Optional[str] = Field(
        default=None,
        description="Google maps place ID",
    )

    name: str = Field(
        description="地點名稱",
        examples=["台北101", "故宮博物院"]
    )

    rating: float = Field(
        ge=0.0,               # 最小值
        le=5.0,               # 最大值
        default=0.0,          # 預設值
        description="地點評分 (0.0-5.0分)",
        examples=[4.5, 3.8]
    )

    lat: float = Field(
        ge=-90.0,            # 地理範圍限制
        le=90.0,
        description="緯度座標",
        examples=[25.0339808]
    )

    lon: float = Field(
        ge=-180.0,           # 地理範圍限制
        le=180.0,
        description="經度座標",
        examples=[121.561964]
    )

    duration: Optional[int] = Field(
        ge=0,                # 不可為負數
        default=None,        # 先設為 None,讓 __init__ 處理預設值
        description="建議停留時間(分鐘)",
    )

    duration_min: Optional[int] = None

    label: str = Field(
        default="景點",
        description="地點類型標籤",
    )

    period: str = Field(
        description="適合遊玩的時段",
        examples=["morning", "lunch", "afternoon", "dinner", "night"]
    )

    hours: Dict[int, Optional[Any]] = Field(
        description="""營業時間資訊，格式：
        {
            1: [{'start': '09:00', 'end': '17:00'}],  # 週一
            2: [{'start': '09:00', 'end': '17:00'}],  # 週二
            ...
            7: [{'start': '09:00', 'end': '17:00'}]   # 週日
        }
        - 支援多時段營業(例如中午和晚上)
        - None 表示該日店休
        - 支援跨日營業時間(例如夜市)
        """
    )

    url: Optional[str] = Field(
        default=None,
        description="地點的導航連結",
        examples=["https://example.com/route?..."]
    )

    def __init__(self, **data):
        # 檢查是否有 duration 或 duration_min
        if 'duration' not in data and 'duration_min' in data:
            data['duration'] = data['duration_min']
        elif 'duration' not in data:
            data['duration'] = 60  # 預設60分鐘

        # 為了相容性,確保 duration_min 也有值
        data['duration_min'] = data['duration']

        super().__init__(**data)

    @field_validator('period')
    def validate_period(cls, v: str) -> str:
        """驗證時段標記的正確性"""
        valid_periods = {'morning', 'lunch', 'afternoon', 'dinner', 'night'}
        if v not in valid_periods:
            raise ValueError(f'無效的時段標記: {v}')
        return v

    @field_validator('label')
    def validate_label(cls, v):
        """驗證label格式"""
        if pd.isna(v):  # 檢查是否為NaN
            return "未分類"
        return str(v)  # 確保轉換為字串

    @model_validator(mode='before')
    def validate_hours(cls, values: Dict) -> Dict:
        """前處理驗證

        特殊規則:
        1. 如果hours完全沒有資料 -> 全部24小時營業
        2. 如果1-7都是None或'none' -> 全部24小時營業  
        3. 如果部分天數有資料 -> 沒設定的視為休息(None)
        """
        if 'hours' not in values:
            values['hours'] = {i: [{'start': '00:00', 'end': '23:59'}]
                               for i in range(1, 8)}
            return values

        hours = values['hours']

        # 檢查是否全部都是None或'none'
        all_closed = True
        for day in range(1, 8):
            value = hours.get(day)
            if value not in [None, 'none', []]:
                all_closed = False
                break

        if all_closed:
            # 全部都是None -> 改成24小時
            values['hours'] = {i: [{'start': '00:00', 'end': '23:59'}]
                               for i in range(1, 8)}
            return values

        # 處理每一天
        processed = {}
        for day in range(1, 8):
            if day not in hours:
                processed[day] = None
                continue

            value = hours[day]
            if value in [None, 'none', []]:
                processed[day] = None
            else:
                if not isinstance(value, list):
                    value = [value]
                value = [
                    slot if isinstance(slot, dict) else {
                        'start': slot['start'], 'end': slot['end']}
                    for slot in value
                ]
                processed[day] = value

        values['hours'] = processed
        return values

    @field_validator('lat', 'lon')
    def validate_coordinates(cls, v: float, field: str) -> float:
        """驗證座標範圍"""
        # 使用新的驗證器
        if not TripValidator.validate_coordinates(
            v if field == 'lat' else 0,
            0 if field == 'lat' else v
        ):
            raise ValueError(f"{field} 座標錯誤: 超出有效範圍")
        return v

    def calculate_distance(self, other: Union['PlaceDetail', Dict]) -> float:
        """計算與另一個地點的距離

        Args:
            other: 另一個地點
                - 可以是 PlaceDetail 物件
                - 或包含 lat/lon 的字典

        Returns:
            float: 兩點間距離(公里)

        Examlpes:
            >>> place1 = PlaceDetail(...)
            >>> place2 = PlaceDetail(...)
            >>> distance = place1.calculate_distance(place2)
            >>> # 或是使用字典
            >>> point = {'lat': 25.0, 'lon': 121.5}
            >>> distance = place1.calculate_distance(point)
        """
        from ..services.geo_service import GeoService

        # 將自己的座標轉換為字典格式
        self_dict = {
            'lat': float(self.lat),  # 確保是浮點數
            'lon': float(self.lon)
        }

        # 如果另一個地點是字典，直接使用
        if isinstance(other, dict):
            other_dict = {
                'lat': float(other['lat']),  # 確保是浮點數
                'lon': float(other['lon'])
            }
        else:
            # 如果是 PlaceDetail 物件，轉換為字典
            other_dict = {
                'lat': float(other.lat),
                'lon': float(other.lon)
            }

        return GeoService.calculate_distance(self_dict, other_dict)

    def is_open_at(self, day: int, time_str: str) -> bool:
        """檢查指定時間是否在營業時間內

        Args:
            day: 1-7 代表週一到週日
            time_str: "HH:MM" 格式時間

        Returns:
            bool: True表示營業中,False表示不營業
        """
        # 檢查該天是否有營業時間設定
        if not self.hours or day not in self.hours:
            return False

        # 檢查時段是否有效
        time_slots = self.hours[day]
        if not time_slots or not isinstance(time_slots, list):
            return False

        check_time = datetime.strptime(
            time_str,
            TimeService.TIME_FORMAT
        ).time()

        for slot in time_slots:
            if not slot or not isinstance(slot, dict):
                continue

            # 確保slot有start和end
            if 'start' not in slot or 'end' not in slot:
                continue

            try:
                start = datetime.strptime(
                    slot['start'], TimeService.TIME_FORMAT
                ).time()
                end = datetime.strptime(
                    slot['end'], TimeService.TIME_FORMAT
                ).time()
            except ValueError:
                continue

            if TimeService.is_time_in_range(check_time, start, end, allow_overnight=True):
                return True

        return False

    def is_suitable_for_current_time(self, current_time: datetime) -> bool:
        """檢查當前時間是否適合遊玩此地點

        根據用餐時間劃分時段：
        - 中餐時間前是上午的行程
        - 中餐時間前後一小時是中餐行程
        - 中餐後是下午行程
        - 晚餐時間前後一小時是晚餐行程
        - 晚餐後是晚上行程

        Args:
            current_time (datetime): 要檢查的時間

        Returns:
            bool: True 表示適合，False 表示不適合
        """
        from ..services.time_service import TimeService

        time_service = TimeService(
            lunch_time="12:00",   # 預設中餐時間
            dinner_time="18:00"   # 預設晚餐時間
        )

        # 取得當前的時段
        current_period = time_service.get_current_period(current_time)

        # 檢查當前時段是否符合景點的建議遊玩時段
        return current_period == self.period

    def get_next_available_time(self, current_day: int, current_time: str) -> Optional[Dict]:
        """取得下一個營業時間

        Args:
            current_day: 1-7代表週一到週日
            current_time: "HH:MM"格式時間

        Returns:
            Dict: {
                'day': int,
                'start': str,
                'end': str
            }
        """
        current = datetime.strptime(
            current_time, TimeService.TIME_FORMAT).time()

        for day_offset in range(7):
            check_day = ((current_day - 1 + day_offset) % 7) + 1
            slots = self.hours.get(check_day, [])

            if not slots or slots[0] is None:
                continue

            for slot in slots:
                if slot is None:
                    continue

                start_time = datetime.strptime(slot['start'],
                                               TimeService.TIME_FORMAT).time()

                if day_offset == 0 and start_time <= current:
                    continue

                return {
                    'day': check_day,
                    'start': slot['start'],
                    'end': slot['end']
                }

        return None
