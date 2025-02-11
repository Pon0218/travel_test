from datetime import datetime
from zoneinfo import ZoneInfo

def Second(data):
    current_date = datetime.now(ZoneInfo('Asia/Taipei')).strftime("%Y/%m/%d")
    
    # 定義交通方式對應的圖示
    transport_icons = {
        "大眾運輸": "🚌",
        "開車": "🚗",
        "騎車": "🛵",
        "步行": "🚶"
    }
    
    # 定義顯示樣式
    location = {
        "type": "text",
        "text": "地點",
        "size": "sm",
        "align": "start",
        "wrap": False,
        "flex": 3,
        "maxLines": 2,
        "color": "#555555"
    }
    
    H = {
        "type": "text",
        "text": "00:00-00:00",
        "size": "sm",
        "align": "start",
        "flex": 2,
        "adjustMode": "shrink-to-fit",
        "color": "#666666"
    }

    contents = []
    for i in range(len(data)):
        temp_loc = location.copy()
        temp_loc['text'] = data[i]["name"]
        
        temp_H = H.copy()
        temp_H["text"] = '-'.join([data[i]['start_time'], data[i]['end_time']])
        
        # 交通圖示和時間
        transport_icon = transport_icons.get(data[i]['transport']['mode'], "🚗")
        
        # 合併營業時間和交通時間在同一行
        time_transport_info = {
            "type": "box",
            "layout": "horizontal",
            "contents": [
                {
                    "type": "text",
                    "text": f"{transport_icon} {data[i]['transport']['time']}分鐘",
                    "size": "xs",
                    "color": "#7B8994",
                    "align": "end",
                    "flex": 4
                },
                {
                    "type": "text",
                    "text": f"⏰ {data[i]['hours']['start']}-{data[i]['hours']['end']}",
                    "size": "xs",
                    "color": "#7B8994",
                    "flex": 6
                }
            ],
            "margin": "sm"
        }

        # 精簡的地點容器
        location_container = {
            "type": "box",
            "layout": "vertical",
            "spacing": "none",
            "margin": "sm",
            "contents": [
                {
                    "type": "box",
                    "layout": "horizontal",
                    "spacing": "md",
                    "contents": [
                        temp_H,
                        temp_loc
                    ]
                },
                time_transport_info
            ],
            "paddingBottom": "sm"
        }

        contents.append(location_container)

    # Second_bubble 設定
    Second_bubble = {
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

    # 地點列表容器（精簡版）
    cot = {
        "type": "box",
        "layout": "vertical",
        "spacing": "none",
        "margin": "md",
        "contents": contents
    }

    Second_bubble['body']['contents'].append(cot)

    return Second_bubble