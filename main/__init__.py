"""
初始化 main 套件
提供主要的控制器和程式進入點
"""
# main/__init__.py
from main.main_trip.trip_service import run_trip_planner
from main.main_trip.controllers.controller import TripController, init_config

__all__ = [
    'run_trip_planner',
    'TripController',
    'init_config'
]
