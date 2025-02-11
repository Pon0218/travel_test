# tests/test_cases/utils/test_system_set_default.py

import unittest
from datetime import datetime
from feature.trip import TripPlanningSystem


class TestTripPlanningSystem(unittest.TestCase):
    def setUp(self):
        self.system = TripPlanningSystem()

    def test_default_values(self):
        """測試完全使用預設值的情況"""
        result = self.system._set_defaults({})

        self.assertEqual(result['start_time'], "09:00")
        self.assertEqual(result['end_time'], "21:00")
        self.assertEqual(result['start_point'], "台北車站")
        self.assertEqual(result['end_point'], None)
        self.assertEqual(result['transport_mode'], "driving")
        self.assertEqual(result['distance_threshold'], 30)
        self.assertEqual(result['lunch_time'], "12:00")
        self.assertEqual(result['dinner_time'], "19:00")

    def test_lunch_time_scenarios(self):
        """測試不同開始時間對午餐時間的影響"""
        # Case 1: 正常開始時間(09:00)
        result = self.system._set_defaults({"start_time": "09:00"})
        self.assertEqual(result['lunch_time'], "12:00")

        # Case 2: 接近午餐時間開始(11:30)
        result = self.system._set_defaults({"start_time": "11:30"})
        self.assertEqual(result['lunch_time'], "12:00")

        # Case 3: 午餐時間後開始(13:30)
        result = self.system._set_defaults({"start_time": "13:30"})
        self.assertEqual(result['lunch_time'], None)

        # Case 4: 午餐時間開始(12:00)
        result = self.system._set_defaults({"start_time": "12:00"})
        self.assertEqual(result['lunch_time'], "12:30")

    def test_dinner_time_scenarios(self):
        """測試不同結束時間對晚餐時間的影響"""
        # Case 1: 早於最早晚餐時間結束(16:00)
        result = self.system._set_defaults({"end_time": "16:00"})
        self.assertEqual(result['dinner_time'], None)

        # Case 2: 介於最早晚餐和最晚晚餐時間之間結束(18:00)
        result = self.system._set_defaults({"end_time": "18:00"})
        self.assertEqual(result['dinner_time'], "16:30")

        # Case 3: 介於最晚晚餐和21:30之間結束(21:00)
        result = self.system._set_defaults({"end_time": "21:00"})
        self.assertEqual(result['dinner_time'], "19:00")

        # Case 4: 晚於21:30結束(22:00)
        result = self.system._set_defaults({"end_time": "22:00"})
        self.assertEqual(result['dinner_time'], "20:00")

    def test_special_scenarios(self):
        """測試特殊情況"""
        # Case 1: 很早結束的行程
        result = self.system._set_defaults({
            "start_time": "08:00",
            "end_time": "11:00"
        })
        self.assertEqual(result['lunch_time'], None)
        self.assertEqual(result['dinner_time'], None)

        # Case 2: 很晚開始的行程
        result = self.system._set_defaults({
            "start_time": "14:00",
            "end_time": "22:00"
        })
        self.assertEqual(result['lunch_time'], None)
        self.assertEqual(result['dinner_time'], "20:00")

        # Case 3: 短時間行程
        result = self.system._set_defaults({
            "start_time": "11:30",
            "end_time": "12:30"
        })
        self.assertEqual(result['lunch_time'], "12:00")
        self.assertEqual(result['dinner_time'], None)

    def test_none_values(self):
        """測試處理None值的情況"""
        result = self.system._set_defaults({
            "start_time": None,
            "end_time": None,
            "lunch_time": None,
            "dinner_time": None
        })

        # 應該使用預設值
        self.assertEqual(result['start_time'], "09:00")
        self.assertEqual(result['end_time'], "21:00")
        self.assertEqual(result['lunch_time'], "12:00")
        self.assertEqual(result['dinner_time'], "19:00")


if __name__ == '__main__':
    unittest.main()
