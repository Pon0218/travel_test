from datetime import datetime
import re

# ---------邏輯函式----------------------------------

def is_float(value:any) -> bool:
    '''
    判斷是否為 "正的" 浮點數
    '''
    try:
        float(value)
        valid = value > 0
        return valid
    except :
        return False

def is_valid_24_hour_time(time_str:str) -> bool:
    '''
    判斷是否為 24 小時制
    '''
    try :
        pattern = r"^(?:[01]\d|2[0-3]):[0-5]\d|24:00$"
        valid = re.fullmatch(pattern, time_str) is not None
        return valid
    except :
        return False

def is_valid_mm_dd(date_str: str) -> bool:
    '''
    判斷是否為日期格式
    '''
    try:
        datetime.strptime(date_str, "%m-%d")
        return True
    except :
        return False

def is_valid_lat_lon(lat_lon)-> bool:
    '''
    判斷是否為經緯度
    '''
    try:
        lat, lon = lat_lon
        valid = -90 <= lat <= 90 and -180 <= lon <= 180
        return valid
    except:
        return False

def is_valid_one_to_seven(value: any)-> bool:
    '''
    確認數值是否為 1-7
    '''
    try:
        valid = isinstance(value, int) and 1 <= value <= 7
        return valid
    except:
        return False

if __name__ == "__main__":
    # ----------------測試正的 float 判斷--------------------------------------
    print('----------------測試正的 float 判斷--------------------------------------')
    print(is_float(3.14))  # True
    print(is_float(-2.71)) # False
    print(is_float("abc"))   # False
    print(is_float(10))    # True
    
    # ----------------是否為 24 小時制測試---------------------
    print('----------------是否為 24 小時制測試---------------------')
    print(is_valid_24_hour_time("00:00"))  # True
    print(is_valid_24_hour_time("23:59"))  # True
    print(is_valid_24_hour_time("24:00"))  # True
    print(is_valid_24_hour_time("24:01"))  # False
    print(is_valid_24_hour_time("12:60"))  # False
    print(is_valid_24_hour_time("-01:30")) # False


    # ----------------測試 mm-dd 日期格式-------------------------------------------
    print('----------------測試 mm-dd 日期格式-------------------------------------------')
    print(is_valid_mm_dd("01-01"))  # True
    print(is_valid_mm_dd("12-31"))  # True
    print(is_valid_mm_dd("02-30"))  # False
    print(is_valid_mm_dd("13-01"))  # False
    print(is_valid_mm_dd("00-10"))  # False

    # ----------------測試 經緯度數值--------------------------------------------------
    print('----------------測試 經緯度數值--------------------------------------------------')
    print( is_valid_lat_lon((25.033, 121.565)) )  # True（台北101）
    print( is_valid_lat_lon((-91, 100)) )  # False（緯度超出範圍）
    print( is_valid_lat_lon((45, 190)) )  # False（經度超出範圍）
    print( is_valid_lat_lon('abx') )

    # -----------------測試 1-7 數值判斷-----------------------------------------
    print('-----------------測試 1-7 數值判斷-----------------------------------------')
    print(is_valid_one_to_seven(3))  # True
    print(is_valid_one_to_seven(7))  # True
    print(is_valid_one_to_seven(0))  # False
    print(is_valid_one_to_seven(8))  # False
    print(is_valid_one_to_seven("5"))  # False (字串)
