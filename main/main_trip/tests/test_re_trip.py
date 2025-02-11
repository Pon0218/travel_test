# test_trip_planner.py

import pytest
from datetime import datetime

from main.main_trip.controllers.controller import TripController, init_config


def create_mock_trip():
    """建立模擬行程資料"""
    return [
        {
            'step': 0,
            'name': '台北車站',
            'label': '起點',
            'start_time': '09:00',
            'end_time': '09:00',
            'period': 'morning',
            'hours': {'1': [{'start': '00:00', 'end': '23:59'}]},  # 加入營業時間
            'lat': 25.0478,  # 加入座標
            'lon': 121.5170
        },
        {
            'step': 1,
            'name': '西門紅樓',
            'label': '景點',
            'start_time': '09:15',
            'end_time': '10:15',
            'period': 'morning',
            'hours': {'1': [{'start': '09:00', 'end': '21:00'}]},
            'lat': 25.0421,
            'lon': 121.5079,
            'duration': 60
        },
        {
            'step': 2,
            'name': '龍山寺',
            'label': '景點',
            'start_time': '10:30',
            'end_time': '11:30',
            'period': 'morning',
            'hours': {'1': [{'start': '09:00', 'end': '21:00'}]},
            'lat': 25.0374,
            'lon': 121.4999,
            'duration': 60
        }
    ]


def test_replan_from_morning():
    """測試從早上時段重新規劃"""
    # 初始化 controller
    controller = TripController(init_config())

    # 準備原始行程
    previous_trip = create_mock_trip()

    # 從第3個點重新規劃
    restart_index = 3

    # 準備測試資料
    locations = [
        {
            'name': '華山文創園區',
            'label': '景點',
            'period': 'morning',
            'hours': {'1': [{'start': '09:00', 'end': '21:00'}]},
            'lat': 25.0444,
            'lon': 121.5297
        },
        # 加入更多測試用地點...
    ]

    requirement = [{
        "出發時間": "09:00",
        "結束時間": "21:00",
        "出發地點": "台北車站",
        "結束地點": "台北車站",
        "交通方式": "driving",
        "可接受距離門檻(KM)": 30,
        "午餐時間": "12:00",
        "晚餐時間": "18:00"
    }]

    # 直接使用 plan_trip
    new_trip = controller.trip_planner.plan_trip(
        locations,
        requirement,
        previous_trip=previous_trip,
        restart_index=restart_index
    )

    # 驗證結果
    assert len(new_trip) > restart_index, "應該要有新增的行程點"

    # 檢查前面行程是否保留
    for i in range(restart_index):
        assert new_trip[i]['name'] == previous_trip[i]['name']

    # 檢查時間銜接
    last_end = datetime.strptime(
        previous_trip[restart_index-1]['end_time'], '%H:%M')
    next_start = datetime.strptime(
        new_trip[restart_index]['start_time'], '%H:%M')
    assert last_end <= next_start, "新行程的開始時間應該在上一個行程之後"


def test_replan_across_lunch():
    """測試跨午餐時段重新規劃"""
    # 初始化 controller
    controller = TripController(init_config())

    # 建立一個到11:30的行程
    previous_trip = create_mock_trip()
    restart_index = 2

    # 準備午餐時段的測試資料
    locations = [
        {
            'name': '鼎泰豐',
            'label': '餐廳',
            'period': 'lunch',
            'hours': {'1': [{'start': '11:00', 'end': '21:00'}]},
            'lat': 25.0523,
            'lon': 121.5437
        },
        {
            'name': '欣葉台菜',
            'label': '餐廳',
            'period': 'lunch',
            'hours': {'1': [{'start': '11:00', 'end': '21:00'}]},
            'lat': 25.0421,
            'lon': 121.5446
        },
        {
            'name': '華山文創園區',
            'label': '景點',
            'period': 'afternoon',
            'hours': {'1': [{'start': '09:00', 'end': '21:00'}]},
            'lat': 25.0444,
            'lon': 121.5297
        }
    ]

    requirement = [{
        "出發時間": "09:00",
        "結束時間": "21:00",
        "出發地點": "台北車站",
        "結束地點": "台北車站",
        "交通方式": "driving",
        "可接受距離門檻(KM)": 30,
        "午餐時間": "12:00",
        "晚餐時間": "18:00"
    }]

    # 直接使用 plan_trip
    new_trip = controller.trip_planner.plan_trip(
        locations,
        requirement,
        previous_trip=previous_trip,
        restart_index=restart_index
    )

    # 驗證結果
    # 檢查是否有安排午餐
    lunch_arranged = False
    for i in range(restart_index, len(new_trip)):
        if new_trip[i]['period'] == 'lunch':
            lunch_arranged = True
            lunch_time = datetime.strptime(new_trip[i]['start_time'], '%H:%M')
            # 確認午餐時間在合理範圍
            target_lunch = datetime.strptime('12:00', '%H:%M')
            time_diff = abs((lunch_time - target_lunch).total_seconds() / 60)
            assert time_diff <= 60, "午餐時間應該在目標時間一小時內"
            break

    assert lunch_arranged, "應該要安排午餐"


def test_replan_in_same_period():
    """測試同一時段內重新規劃"""
    # 初始化 controller
    controller = TripController(init_config())

    # 建立一個morning時段的行程
    previous_trip = create_mock_trip()
    restart_index = 2

    # 準備同時段(morning)的測試資料
    locations = [
        {
            'name': '中正紀念堂',
            'label': '景點',
            'period': 'morning',
            'hours': {'1': [{'start': '09:00', 'end': '21:00'}]},
            'lat': 25.0367,
            'lon': 121.5214
        },
        {
            'name': '國立歷史博物館',
            'label': '景點',
            'period': 'morning',
            'hours': {'1': [{'start': '09:00', 'end': '17:00'}]},
            'lat': 25.0322,
            'lon': 121.5199
        }
    ]

    requirement = [{
        "出發時間": "09:00",
        "結束時間": "21:00",
        "出發地點": "台北車站",
        "結束地點": "台北車站",
        "交通方式": "driving",
        "可接受距離門檻(KM)": 30,
        "午餐時間": "12:00",
        "晚餐時間": "18:00"
    }]

    # 直接使用 plan_trip
    new_trip = controller.trip_planner.plan_trip(
        locations,
        requirement,
        previous_trip=previous_trip,
        restart_index=restart_index
    )

    # 驗證結果
    # 檢查新的地點是否也是morning時段
    assert new_trip[restart_index]['period'] == 'morning', \
        "同時段重規劃應該維持在相同時段"


if __name__ == '__main__':
    pytest.main(['-v', __file__])
