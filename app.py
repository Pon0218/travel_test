from dotenv import dotenv_values
from flask import Flask, request, abort
from linebot.v3 import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    ReplyMessageRequest,
    TextMessage,
)
from linebot.v3.webhooks import (
    MessageEvent,
    TextMessageContent,
    PostbackEvent,
)

from feature.line import RichMenuManager
from feature.line.handlers import (
    CommandHandler,
    FavoriteHandler,
    RecommendHandler,
    ScenarioHandler,
    user_states,
    user_queries,
    recent_recommendations,
)
from feature.nosql_mongo.mongo_trip.db_helper import trip_db


# 載入 .env 檔案中的環境變數
config = dotenv_values("./.env")
if len(config) == 0:
    print('please check .env path')

# config 環境變數對應轉換器
# 從環境變數或 .env 文件載入配置
import os
config['jina_url'] = os.getenv('jina_url', config.get('jina_url'))
config['jina_headers_Authorization'] = os.getenv('jina_headers_Authorization', config.get('jina_headers_Authorization'))
config['qdrant_url'] = os.getenv('qdrant_url', config.get('qdrant_url'))
config['qdrant_api_key'] = os.getenv('qdrant_api_key', config.get('qdrant_api_key'))
config['ChatGPT_api_key'] = os.getenv('ChatGPT_api_key', config.get('ChatGPT_api_key'))
config['LINE_CHANNEL_SECRET'] = os.getenv('LINE_CHANNEL_SECRET', config.get('LINE_CHANNEL_SECRET'))
config['LINE_CHANNEL_ACCESS_TOKEN'] = os.getenv('LINE_CHANNEL_ACCESS_TOKEN', config.get('LINE_CHANNEL_ACCESS_TOKEN'))
config['GOOGLE_MAPS_API_KEY'] = os.getenv('GOOGLE_MAPS_API_KEY', config.get('GOOGLE_MAPS_API_KEY'))


# 讀取 LINE 的環境變數
LINE_CHANNEL_ACCESS_TOKEN = config["LINE_CHANNEL_ACCESS_TOKEN"]
LINE_CHANNEL_SECRET = config["LINE_CHANNEL_SECRET"]

# 初始化 Flask 應用
app = Flask(__name__)

# 初始化 Configuration, WebhookHandler, RichMenuManager
configuration = Configuration(access_token=LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

try:
    rich_menu_manager = RichMenuManager(LINE_CHANNEL_ACCESS_TOKEN)
    menu_ids = rich_menu_manager.create_rich_menu()
    if menu_ids[0] is None:
        print("Rich Menu 建立失敗,但程式將繼續執行")
    else:
        print("Rich Menu 建立成功")
except Exception as e:
    print(f"Rich Menu 初始化出錯,但程式將繼續執行: {str(e)}")


@app.route("/callback", methods=['POST'])
def callback():
    app.logger.info("Received webhook request")
    app.logger.info(f"Headers: {request.headers}")
    app.logger.info(f"Body: {request.get_data(as_text=True)}")
    # 取得 X-Line-Signature 標頭值
    signature = request.headers['X-Line-Signature']

    # 取得請求的 body 內容
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # 簽名驗證
    try:
        handler.handle(body, signature)  # 使用 handler 來處理簽名驗證
    except InvalidSignatureError:
        app.logger.error(
            "Invalid signature. Please check your channel access token/channel secret.")
        abort(400)  # 若簽名無效，返回 400 錯誤碼

    return 'OK'


@handler.add(PostbackEvent)
def handle_postback(event):
    """處理postback事件

    Args:
        event: LINE postback event


    當用戶點擊X按鈕時觸發,格式為:
    cancel_{plan_index}_{step}_{name}_{label}

    範例:
    - cancel_3_5_遼寧街夜市_夜市 
    表示第3個行程的第5個景點
    """
    try:
        with ApiClient(configuration) as api_client:
            messaging_api = MessagingApi(api_client)
            command_handler = CommandHandler(messaging_api, app.logger)

            data = event.postback.data
            line_id = event.source.user_id

            if data.startswith("action=trip_planning"):
                command_handler.handle_trip_command(event, None, line_id)

            elif data.startswith("cancel_"):
                # 解析出地點index和資訊
                parts = data.split("_")
                if len(parts) != 5:
                    print("按鈕格式錯誤: {data}")
                    return

                _, plan_index, step, name, label = parts
                plan_index = int(plan_index)
                step = int(step)

                # 更新行程的restart_index
                button_id = f"cancel_{plan_index}_{step}"
                success = trip_db.update_plan_restart_index(
                    line_id=line_id,
                    plan_index=plan_index,
                    restart_index=step,
                    button_id=button_id,
                )
                print(f"更新結果: {success}, button_id: {button_id}")

                if success:
                    # 更新用戶偏好
                    dislike_reason = f"我不喜歡{name}({label})"
                    trip_db.update_user_dislike(line_id, dislike_reason)

                    dislike_button_text = f"已紀錄您不喜歡{name}({label})"
                else:
                    dislike_button_text = f"別再按啦! 我已經知道您不喜歡{name}({label})"

                messaging_api.reply_message(
                    ReplyMessageRequest(
                        reply_token=event.reply_token,
                        messages=[TextMessage(text=dislike_button_text)]
                    )
                )

    except Exception as e:
        app.logger.error(f"處理postback時發生錯誤: {str(e)}")
        try:
            with ApiClient(configuration) as api_client:
                messaging_api = MessagingApi(api_client)
                messaging_api.reply_message_with_http_info(
                    ReplyMessageRequest(
                        reply_token=event.reply_token,
                        messages=[TextMessage(text="處理請求時發生錯誤，請稍後再試")]
                    )
                )
        except Exception as inner_e:
            app.logger.error(f"Error sending error message: {str(inner_e)}")


@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    """處理使用者傳送的文字訊息

    Args:
        event: LINE message event
    """
    text_message = event.message.text

    try:
        line_id = event.source.user_id
    except Exception:
        line_id = 'none_line_id'

    if trip_db.record_user_input(line_id, text_message):
        print(f"已記錄{line_id}說:{text_message}")

    try:
        with ApiClient(configuration) as api_client:
            messaging_api = MessagingApi(api_client)
            command_handler = CommandHandler(messaging_api, app.logger)
            scenario_handler = ScenarioHandler(
                messaging_api, config, app.logger)
            recommend_handler = RecommendHandler(
                messaging_api, config, app.logger)
            favorite_handler = FavoriteHandler(
                messaging_api, config, app.logger)

            # 解析與處理指令
            command, parameter = command_handler.parse_command(text_message)

    # ======================================================以下是使用說明
            if command == "使用說明":
                command_handler.handle_help_command(event)
            elif command == "旅遊規劃說明":
                command_handler.handle_trip_help(event)
            elif command == "情境搜索說明":
                command_handler.handle_search_help(event)

    # ======================================================以下是旅遊推薦
            elif command == "旅遊推薦":
                command_handler.handle_trip_command(event, parameter, line_id)
            elif command == "紀錄初始化":
                command_handler.handle_init_command(event, line_id)

    # ======================================================以下是情境搜索

            # 情境搜索相關功能處理
            elif command == "我想進行情境搜索":
                scenario_handler.handle_scenario_search(event)

            # 處理情境搜索的查詢輸入
            elif line_id in user_states:
                scenario_handler.handle_user_query(event)

            # 處理顯示收藏
            elif command == "顯示我的收藏":
                favorite_handler.show_favorites(
                    event, recent_recommendations)

            # 處理收藏店家
            elif command.startswith("收藏店家:"):
                favorite_handler.add_favorite(
                    event, recent_recommendations)

            # 處理移除收藏
            elif command.startswith("移除"):
                favorite_handler.remove_favorite(event)

            # 處理推薦其他店家
            elif command == "推薦其他店家":
                recommend_handler.recommend_others(
                    event,
                    recent_recommendations,
                    user_queries,
                )

    except Exception as e:
        app.logger.error(f"Error handling message: {str(e)}")
        try:
            with ApiClient(configuration) as api_client:
                messaging_api = MessagingApi(api_client)
                messaging_api.reply_message_with_http_info(
                    ReplyMessageRequest(
                        reply_token=event.reply_token,
                        messages=[TextMessage(text="處理訊息時發生錯誤，請稍後再試")]
                    )
                )
        except Exception as inner_e:
            app.logger.error(f"Error sending error message: {str(inner_e)}")


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8080)
