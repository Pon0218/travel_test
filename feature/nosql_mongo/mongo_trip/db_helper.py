"""MongoDB存取輔助模組

只匯出資料庫操作handler的實例,
讓其他程式可以直接使用trip_db操作。
"""

from .mongodb_handler import TripDBHandler

# 直接匯出handler實例
trip_db = TripDBHandler()
