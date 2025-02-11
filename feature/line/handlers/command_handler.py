"""
處理LINE Bot的command解析與執行

負責:
1. Command字串解析
2. 執行對應的command邏輯
3. 處理LINE訊息回覆
"""

from linebot.v3.messaging import (
    MessagingApi,
    ReplyMessageRequest,
    TextMessage, FlexMessage,
    FlexContainer
)
from linebot.v3.webhooks import MessageEvent
from typing import Tuple
from feature.line.bubbles_seting import First
from feature.nosql_mongo.mongo_trip.db_helper import trip_db
from main.main_trip.trip_service import run_trip_planner


class CommandHandler:
    """LINE Bot指令處理器"""

    def __init__(self, messaging_api: MessagingApi, logger=None):
        """初始化

        Args:
            messaging_api: LINE Bot的MessagingApi實例
            logger: 可選的logger實例,用於記錄訊息
        """
        self.messaging_api = messaging_api
        self.logger = logger

    def parse_command(self, text: str) -> Tuple[str, str]:
        """解析使用者輸入的command和參數

        Args:
            text: 使用者輸入文字

        Returns:
            tuple[str, str]: (command, parameter)
            - command: 指令名稱,如果非指令則為原始文字
            - parameter: 參數內容,沒有參數則為None
        """
        # 判斷旅遊推薦指令
        # 允許純"旅遊推薦"或"旅遊推薦 XXX"兩種格式
        if text == "旅遊推薦" or text == "旅遊規劃":
            return "旅遊推薦", None
        if text.startswith("旅遊推薦") or text.startswith("旅遊規劃"):
            if not text.startswith("旅遊規劃說明"):
                return "旅遊推薦", text[4:].strip()

        # 判斷記錄初始化指令
        # 只接受純"記錄初始化"五個字
        if text == "記錄初始化" or text == "紀錄初始化":
            return "紀錄初始化", None

        # 其他指令直接返回原始文字,無參數
        return text, None

    def handle_trip_command(self,
                            event: MessageEvent,
                            parameter: str,
                            line_id: str):
        """處理旅遊推薦指令

        Args:
            event: LINE message event
            parameter: 使用者輸入的參數,可能為None 
            line_id: 使用者LINE ID
        """
        try:


            latest = trip_db.get_latest_plan(line_id)
            if latest:
                plan_index = latest.get('plan_index', 1)
            else:
                plan_index = 0

            # 沒有參數時直接傳line_id
            if parameter is None:
                data = run_trip_planner(text="隨便規劃台北一日遊", line_id=line_id)
            else:
                data = run_trip_planner(text=parameter, line_id=line_id)

            carousel = {
                "type": "carousel",
                "contents": [First(data, plan_index + 1)]
            }

            flex_message = FlexMessage(
                alt_text="一日遊行程",
                contents=FlexContainer.from_dict(carousel)
            )

            self.messaging_api.reply_message_with_http_info(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[flex_message]
                )
            )
        except Exception as e:
            if self.logger:
                self.logger.error(f"處理旅遊推薦時發生錯誤: {str(e)}")
            self.messaging_api.reply_message_with_http_info(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[TextMessage(text="處理旅遊推薦時發生錯誤，請稍後再試")]
                )
            )

    def handle_init_command(self,
                            event: MessageEvent,
                            line_id: str):
        """處理紀錄初始化指令

        Args:
            event: LINE message event
            line_id: 使用者LINE ID
        """
        try:
            success = trip_db.clear_user_data(line_id)
            message = "初始化成功" if success else "初始化錯誤，請稍後再試"

            self.messaging_api.reply_message_with_http_info(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[TextMessage(text=message)]
                )
            )
        except Exception as e:
            if self.logger:
                self.logger.error(f"處理紀錄初始化時發生錯誤: {str(e)}")
            self.messaging_api.reply_message_with_http_info(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[TextMessage(text="處理紀錄初始化時發生錯誤，請稍後再試")]
                )
            )

    def handle_help_command(self, event):
        """快速功能介紹"""

        self._send_text_message(event.reply_token, HELP_TEXT)

    def handle_trip_help(self, event):
        """旅遊規劃功能說明"""

        self._send_text_message(event.reply_token, TRIP_HELP)

    def handle_search_help(self, event):
        """情境搜索功能說明"""

        self._send_text_message(event.reply_token, SEARCH_HELP)

    def _send_text_message(self, reply_token: str, text: str):
        """發送文字訊息"""
        try:
            self.messaging_api.reply_message_with_http_info(
                ReplyMessageRequest(
                    reply_token=reply_token,
                    messages=[TextMessage(text=text)]
                )
            )
        except Exception as e:
            print(f"發送說明訊息失敗: {str(e)}")


HELP_TEXT = """歡迎使用智慧旅遊助手!
本系統提供兩種方式幫您探索台北:

旅遊規劃:為您安排完整的一日遊行程,只要分享您想去的地方和喜好即可。

情境搜索:當您想找特定類型的景點時,能提供更精準的推薦。

請選擇功能選單或直接輸入您的旅遊需求開始使用。"""


TRIP_HELP = """✨ 旅遊規劃使用說明:

1. 輸入旅遊需求(選填)
   - 直接描述想去的地方
   - 可加入交通、時間等需求
   - 也可以分享位置

2. 開始規劃 (約需7-10秒)
   - 點選規劃行程按鈕
   - 或輸入「旅遊規劃」+您的需求

3. 重新規劃
   - 文字輸入您新的需求，或點選 × 可以記錄不喜歡的地點
   - 下次規劃會自動避開相似景點
   - 透過按鈕或文字再次呼叫2. 開始規劃

隨時都能重新規劃，也可以用「記錄初始化」清除歷史紀錄。"""

SEARCH_HELP = """✨ 情境搜索使用方式:
開始搜索:按下去之後開始情境搜索功能，需要您輸入需求，例如:我想要淡水的文青咖啡廳、我想要九份的好吃小吃店等等。

收藏:可以把您喜歡的點位收藏起來~最多10個。如果超過收藏會把最舊的收藏覆蓋過去。

我的收藏:將您收藏過的地點呈現出來，並且可以指定刪除點位。

再推薦:對於本次呈現的結果不滿意可以按下【再推薦】，我們會依照該次的需求重新推薦適合的10個點位給您!"""
