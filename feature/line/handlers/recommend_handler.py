"""
處理LINE Bot其他推薦功能

負責:
1. 處理"推薦其他店家"請求 
2. 更新推薦結果
"""

from linebot.v3.messaging import MessagingApi, ReplyMessageRequest, TextMessage, FlexMessage, FlexContainer
from linebot.v3.webhooks import MessageEvent
from feature.nosql_mongo.mongo_rec.mongoDB_ctrl_disat import MongoDBManage_unsatisfied
from feature.line.rec_bubble_setting.change_format import transform_location_data
from feature.line.rec_bubble_setting.line_bubble_changer import generate_flex_messages
from feature.line.rec_bubble_setting.query_metadata_enricher import enrich_query
from main.main_plan.rerun_reccomend import rerun_rec
from pprint import pprint


class RecommendHandler:
    """其他推薦功能處理器"""

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

    def recommend_others(self, event: MessageEvent,
                         recent_recommendations: dict,
                         user_queries: dict):
        """處理推薦其他店家請求

        Args:
            event: LINE message event
            recent_recommendations: 當前的推薦結果字典
            user_queries: 使用者查詢記錄字典
        """
        user_id = event.source.user_id
        messaging_api = self.messaging_api
        config = self.config

        try:
            transformed_data = recent_recommendations.get(user_id, {})
            if not transformed_data:
                messaging_api.reply_message(
                    ReplyMessageRequest(
                        reply_token=event.reply_token,
                        messages=[TextMessage(text="請先進行情境搜索")]
                    )
                )
                return

            # 取得目前要加入 black_list 的 place_ids
            place_ids = list(transformed_data.keys())
            
            # 修改 mongodb 操作部分
            mongodb_obj = MongoDBManage_unsatisfied(config)
            try:
                mongodb_obj.test_connection()
                original_query = user_queries.get(user_id, {}) #定位到最新的query_info
                query_info = enrich_query(original_query, place_ids) #將再推薦的place id丟進去
                if not mongodb_obj.check_user_exists(user_id): #判斷line_user
                    mongodb_obj.add_unsatisfied(query_info)
                else:
                    mongodb_obj.update_blacklist(user_id, place_ids)

                print(f"Original black list count:{len(original_query["black_list"])}")
                print(f"Complete black list count:{len(query_info["black_list"])}")
                print(f"Place IDs being added: {place_ids}")

                # 重新執行推薦
                final_results = rerun_rec(query_info, config)

                transformed_data = transform_location_data(final_results)
                
                recent_recommendations[user_id] = transformed_data
                user_records = mongodb_obj.get_user_records(user_id)  # 返回 List[Dict]
                user_queries[user_id] = user_records[0]  # 取出唯一的 Dict


                flex_messages = generate_flex_messages(transformed_data)
                flex_message = FlexMessage(
                    alt_text="為您推薦其他地點",
                    contents=FlexContainer.from_dict(flex_messages)
                )
                
                messaging_api.reply_message(
                    ReplyMessageRequest(
                        reply_token=event.reply_token,
                        messages=[flex_message]
                    )
                )

            finally:
                mongodb_obj.close()

        except Exception as e:
            if self.logger:
                self.logger.error(f"推薦其他店家時發生錯誤: {str(e)}")
            self._send_error_message(event.reply_token)

    def _send_text_message(self, reply_token: str, text: str):
        """發送文字訊息

        Args:
            reply_token: LINE的回覆token
            text: 要發送的文字
        """
        self.messaging_api.reply_message(
            ReplyMessageRequest(
                reply_token=reply_token,
                messages=[TextMessage(text=text)]
            )
        )

    def _send_error_message(self, reply_token: str):
        """發送錯誤訊息

        Args:
            reply_token: LINE的回覆token
        """
        try:
            self.messaging_api.reply_message(
                ReplyMessageRequest(
                    reply_token=reply_token,
                    messages=[TextMessage(text="系統錯誤，請稍後再試")]
                )
            )
        except Exception as e:
            if self.logger:
                self.logger.error(f"發送錯誤訊息失敗: {str(e)}")
