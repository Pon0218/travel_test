from datetime import datetime
from zoneinfo import ZoneInfo

def Third(data):
    current_date = datetime.now(ZoneInfo('Asia/Taipei')).strftime("%Y/%m/%d")
    
    # 定義顯示樣式
    location = {
        "type": "text",
        "text": "地點",
        "size": "sm",
        "align": "start",
        "wrap": True,
        "flex": 1,
        "maxLines": 2,
        "color": "#555555",
        "weight": "regular"
    }
    
    time = {
        "type": "text",
        "text": "00:00-00:00",
        "size": "xs",
        "align": "start",
        "color": "#7B8994",
        "margin": "sm"
    }

    contents = []
    for i in range(len(data)):
        temp_loc = location.copy()
        temp_loc['text'] = data[i]["name"]

        temp_time =time.copy()
        temp_time["text"] = f"🕒 {data[i]['hours']['start']}-{data[i]['hours']['end']}"

        # 精簡的地點容器
        location_container = {
            "type": "box",
            "layout": "vertical",
            "spacing": "none",
            "margin": "sm",
            "contents": [
                temp_loc,temp_time
            ],
            "paddingBottom": "sm"
        }

        contents.append(location_container)

    # Third_bubble 設定
    Third_bubble = {
        "type": "bubble",
        "body": {
            "type": "box",
            "layout": "vertical",
            "spacing": "sm",
            "paddingAll": "lg",
            "backgroundColor": "#F8F9FA",
            "contents": [
                {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        {
                            "type": "text",
                            "text": "Travel recommendations",
                            "weight": "bold",
                            "color": "#2ECC71",
                            "size": "md",
                            "decoration": "none",
                            "align": "center"
                        }
                    ],
                    "backgroundColor": "#E8F8F5",
                    "paddingAll": "sm",
                    "cornerRadius": "lg",
                    "margin": "none"
                },
                {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        {
                            "type": "text",
                            "text": "📍 Taipei City",
                            "weight": "bold",
                            "size": "xxl",
                            "align": "center",
                            "color": "#2C3E50"
                        }
                    ],
                    "margin": "lg"
                },
                {
                    "type": "box",
                    "layout": "horizontal",
                    "contents": [
                        {
                            "type": "text",
                            "text": "📅",
                            "size": "sm",
                            "align": "center"
                        },
                        {
                            "type": "text",
                            "text": current_date,
                            "size": "sm",
                            "color": "#95A5A6",
                            "margin": "sm"
                        }
                    ],
                    "margin": "md",
                    "justifyContent": "center"
                },
                {
                    "type": "separator",
                    "margin": "xl",
                    "color": "#E9ECEF"
                }
            ]
        }
    }

    # 地點列表容器
    cot = {
        "type": "box",
        "layout": "vertical",
        "spacing": "none",
        "margin": "md",
        "contents": contents
    }

    Third_bubble['body']['contents'].append(cot)

    return Third_bubble