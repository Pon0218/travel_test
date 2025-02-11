import pytest
from datetime import time
from feature.trip.src.core.models.place import PlaceDetail
from pydantic import ValidationError


class TestPlaceHours:
    """測試地點營業時間驗證邏輯"""

    def create_basic_place_data(self):
        """建立基本的地點資料"""
        return {
            "name": "測試地點",
            "rating": 4.5,
            "lat": 25.0,
            "lon": 121.0,
            "duration_min": 60,
            "label": "景點",
            "period": "morning"
        }

    @pytest.mark.parametrize("hours,expected", [
        # 測試1: 正常時間
        (
            {1: [{'start': '09:00', 'end': '17:00'}]},
            {i: None if i != 1  # 未設定日期為None
             else [{'start': '09:00', 'end': '17:00'}] for i in range(1, 8)}
        ),
        # 測試2: 店休
        (
            {1: 'none'},
            {i: None for i in range(1, 8)}  # 都設為None
        ),
        # 測試3: 全部店休
        (
            {i: 'none' for i in range(1, 8)},
            {i: [{'start': '00:00', 'end': '23:59'}]
             for i in range(1, 8)}  # 全部none才改24小時
        )
    ])
    def test_valid_hours(self, hours, expected):
        """測試營業時間格式"""
        data = self.create_basic_place_data()
        data['hours'] = hours
        place = PlaceDetail(**data)

        # 只檢查設定的日期
        for day, value in expected.items():
            assert place.hours[day] == value

    def test_default_hours(self):
        """測試預設24小時"""
        data = self.create_basic_place_data()
        data['hours'] = {}  # 空字典
        place = PlaceDetail(**data)

        # 檢查是否都是24小時
        for day in range(1, 8):
            assert place.hours[day] == [{'start': '00:00', 'end': '23:59'}]

    def test_missing_days(self):
        """測試缺少的日期"""
        data = self.create_basic_place_data()
        # 只設定週一和週二
        data['hours'] = {
            1: [{'start': '09:00', 'end': '17:00'}],
            2: [{'start': '09:00', 'end': '17:00'}]
        }
        place = PlaceDetail(**data)

        # 檢查已設定日期
        assert place.hours[1] == [{'start': '09:00', 'end': '17:00'}]
        assert place.hours[2] == [{'start': '09:00', 'end': '17:00'}]
        # 未設定的應為None(休息)
        for day in range(3, 8):
            assert place.hours[day] is None

    def test_none_and_empty(self):
        """測試None和空列表"""
        data = self.create_basic_place_data()
        data['hours'] = {
            1: None,
            2: 'none',
            3: []
        }
        place = PlaceDetail(**data)

        # 都應該是None
        assert place.hours[1] is None
        assert place.hours[2] is None
        assert place.hours[3] is None

        # 其他日期也是None
        for day in range(4, 8):
            assert place.hours[day] is None


if __name__ == "__main__":
    pytest.main(["-v", "-s", __file__])
