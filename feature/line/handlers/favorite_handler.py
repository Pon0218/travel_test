"""
處理LINE Bot收藏相關功能

負責:
1. 顯示收藏清單
2. 新增收藏
3. 移除收藏
"""

from linebot.v3.messaging import MessagingApi, ReplyMessageRequest, TextMessage, FlexMessage, FlexContainer
from linebot.v3.webhooks import MessageEvent

from feature.line.rec_bubble_setting.line_bubble_favo import generate_remove_flex_messages
from feature.nosql_mongo.mongo_rec.mongoDB_ctrl_favo import MongoDBManage_favorite


class FavoriteHandler:
    """收藏功能處理器"""

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

    def show_favorites(self, event: MessageEvent, recent_recommendations: dict):
        """顯示收藏清單

        Args:
            event: LINE message event
            recent_recommendations: 當前的推薦結果字典
        """
        user_id = event.source.user_id

        try:
            mongodb_obj = MongoDBManage_favorite(self.config)

            if mongodb_obj.check_user(user_id):
                favorites = mongodb_obj.show_favorite(user_id)
                if favorites:
                    flex_messages, _ = generate_remove_flex_messages(
                        favorites, user_id)

                    flex_message = FlexMessage(
                        alt_text="您的收藏清單",
                        contents=FlexContainer.from_dict(flex_messages)
                    )

                    self.messaging_api.reply_message(
                        ReplyMessageRequest(
                            reply_token=event.reply_token,
                            messages=[flex_message]
                        )
                    )
                else:
                    self._send_text_message(event.reply_token, "您的收藏夾是空的")
            else:
                self._send_text_message(event.reply_token, "您沒有收藏任何點位")

            mongodb_obj.close()

        except Exception as e:
            if self.logger:
                self.logger.error(f"顯示收藏清單時發生錯誤: {str(e)}")
            self._send_error_message(event.reply_token)

    def add_favorite(self, event: MessageEvent, recent_recommendations: dict):
        """新增收藏

        Args:
            event: LINE message event
            recent_recommendations: 當前的推薦結果字典
        """
        try:
            user_id = event.source.user_id
            place_name = event.message.text.split(":")[1]

            # 從推薦結果中查找地點資訊
            transformed_data = recent_recommendations.get(user_id, {})
            place_info = None
            place_id = None

            # 遍歷字典查找匹配的地點
            for pid, place in transformed_data.items():
                if place["name"] == place_name:
                    place_info = place
                    place_id = pid
                    break

            if place_info:
                # 準備要存入 MongoDB 的資料
                place_data = {
                    "name": place_info["name"],
                    "rating": place_info["rating"],
                    "address": place_info["address"],
                    "location_url": place_info.get("location_url",
                                                   f"https://www.google.com/maps/place/?q=place_id:{place_id}"),
                    "image_url": place_info.get("image_url", "")
                }

                # 初始化 MongoDB 管理器並處理收藏
                mongodb_obj = MongoDBManage_favorite(self.config)

                if mongodb_obj.check_user(user_id):
                    if mongodb_obj.check_place(user_id, place_id):
                        message = f"已收藏過: {place_name}"
                    else:
                        if mongodb_obj.fix_favorite(user_id, place_id, place_data):
                            message = f"已收藏 {place_name}"
                        else:
                            message = "收藏失敗，請稍後再試"
                else:
                    if mongodb_obj.add_user(user_id, place_id, place_data):
                        message = f"已收藏 {place_name}"
                    else:
                        message = "收藏失敗，請稍後再試"

                mongodb_obj.close()
            else:
                message = "找不到該地點的資訊"

            self._send_text_message(event.reply_token, message)

        except Exception as e:
            if self.logger:
                self.logger.error(f"新增收藏時發生錯誤: {str(e)}")
            self._send_error_message(event.reply_token)

    def remove_favorite(self, event: MessageEvent):
        """移除收藏

        Args:
            event: LINE message event
        """
        try:
            user_id = event.source.user_id
            place_name = event.message.text[2:]  # 去掉"移除"兩個字

            mongodb_obj = MongoDBManage_favorite(self.config)

            favorites = mongodb_obj.show_favorite(user_id)
            if favorites:
                place_id = next((pid for pid, data in favorites.items()
                                 if data["name"] == place_name), None)

                if place_id:
                    if self.logger:
                        self.logger.info(
                            f"移除收藏 - 用戶ID: {user_id}, 地點ID: {place_id}")
                    if mongodb_obj.delete_favorite(user_id, place_id):
                        message = f"已刪除: {place_name}"
                    else:
                        message = "刪除失敗，請稍後再試"
                else:
                    message = "找不到該收藏"
            else:
                message = "您沒有任何收藏"

            mongodb_obj.close()

            self._send_text_message(event.reply_token, message)

        except Exception as e:
            if self.logger:
                self.logger.error(f"移除收藏時發生錯誤: {str(e)}")
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
