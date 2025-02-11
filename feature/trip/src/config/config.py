from dotenv import load_dotenv
import os

# 載入環境變數
load_dotenv()

# 為了相容現有程式碼,保持同名變數
GOOGLE_MAPS_API_KEY = os.getenv('GOOGLE_MAPS_API_KEY')

# 驗證必要的設定都存在
if not GOOGLE_MAPS_API_KEY:
    raise ValueError("找不到必要的環境變數: GOOGLE_MAPS_API_KEY")
