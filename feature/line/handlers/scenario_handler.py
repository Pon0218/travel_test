"""
處理LINE Bot情境搜索相關功能

負責:
1. 情境搜索請求處理
2. 收藏相關功能處理  
3. 處理其他推薦請求
"""

from linebot.v3.messaging import MessagingApi, ReplyMessageRequest, TextMessage, FlexMessage, FlexContainer
from linebot.v3.webhooks import MessageEvent
from pprint import pprint

from feature.nosql_mongo.mongo_rec.mongoDB_ctrl_disat import MongoDBManage_unsatisfied
from feature.line.rec_bubble_setting.change_format import transform_location_data
from feature.line.rec_bubble_setting.line_bubble_changer import generate_flex_messages
from main.main_plan.recommandation_service import recommandation

# 儲存狀態用的字典
user_states = {}  # 使用者狀態
recent_recommendations = {}  # 最近推薦結果
user_queries = {}  # 查詢紀錄


class ScenarioHandler:
    """情境搜索功能處理器"""

    def __init__(self, messaging_api: MessagingApi, config: dict, logger=None):
        """初始化

        Args:
            messaging_api: LINE Bot的MessagingApi實例
            config: 設定檔內容
            logger: 可選的logger實例
        """
        self.messaging_api = messaging_api
        self.config = config
        self.logger = logger

    def handle_scenario_search(self, event: MessageEvent):
        """處理情境搜索請求

        Args:
            event: LINE message event
        """
        user_id = event.source.user_id

        try:
            # 初始化並清除舊記錄
            mongodb_obj = MongoDBManage_unsatisfied(self.config)
            mongodb_obj.delete_user_record(user_id)
            mongodb_obj.close()

            # 設定使用者狀態
            global user_states
            user_states[user_id] = "waiting_for_query"

            # 發送提示訊息
            self.messaging_api.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[TextMessage(text="請輸入你的需求(例如:請推薦我淡水好吃的餐廳)")]
                )
            )

        except Exception as e:
            if self.logger:
                self.logger.error(f"處理情境搜索時發生錯誤: {str(e)}")
            self._send_error_message(event.reply_token)

    def handle_user_query(self, event: MessageEvent):
        """處理使用者的查詢輸入

        Args:
            event: LINE message event
        """
        user_id = event.source.user_id
        user_text = event.message.text

        # 檢查是否在等待輸入狀態
        global user_states, recent_recommendations, user_queries
        if user_id not in user_states or user_states[user_id] != "waiting_for_query":
            return False

        # 檢查是否為特殊指令
        if user_text in ['顯示我的收藏', '推薦其他店家'] or \
           user_text.startswith('收藏店家:') or \
           user_text.startswith('移除'):
            self.messaging_api.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[TextMessage(text="請重新輸入你的需求(例如:請推薦我淡水好吃的餐廳)")]
                )
            )
            return True

        try:
            # 清除使用者狀態
            del user_states[user_id]

            # 執行推薦
            final_results, query_info = recommandation(user_text, self.config)

            # 儲存查詢資訊
            query_info["line_user_id"] = user_id
            user_queries[user_id] = query_info

            # 轉換並儲存推薦結果
            transformed_data = transform_location_data(final_results)
            recent_recommendations[user_id] = transformed_data

            # 生成並發送回應
            flex_messages = generate_flex_messages(transformed_data)
            flex_message = FlexMessage(
                alt_text="為您推薦以下地點",
                contents=FlexContainer.from_dict(flex_messages)
            )
            self.messaging_api.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[flex_message]
                )
            )
            return True

        except Exception as e:
            if self.logger:
                self.logger.error(f"處理查詢時發生錯誤: {str(e)}")
                import traceback
                self.logger.error(traceback.format_exc())
            self._send_error_message(event.reply_token)
            return True

    def _send_error_message(self, reply_token: str):
        """發送錯誤訊息

        Args:
            reply_token: LINE的回覆token
        """
        try:
            self.messaging_api.reply_message(
                ReplyMessageRequest(
                    reply_token=reply_token,
                    messages=[TextMessage(text="抱歉，系統處理時發生錯誤，請稍後再試")]
                )
            )
        except Exception as e:
            if self.logger:
                self.logger.error(f"發送錯誤訊息失敗: {str(e)}")
