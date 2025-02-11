from datetime import datetime
from typing import List


def First(data: List[dict], plan_index: int = 1):
    current_date = datetime.strptime(
        data[0]['date'], "%Y-%m-%d").strftime("%Y/%m/%d")

    transport_icons = {
        "大眾運輸": "🚄",
        "開車": "🚗",
        "騎自行車": "🚲",
        "步行": "🚶"
    }

    H = {
        "type": "text",
        "text": "00:00",
        "size": "sm",
        "spacing": "md",
        "align": "center",
        "flex": 2,
        "adjustMode": "shrink-to-fit",
        "color": "#666666",
        "weight": "regular"
    }

    contents = []
    for i in range(len(data)):
        # 生成URL
        location_url = ""
        if data[i].get('place_id'):
            location_url = f"https://www.google.com/maps/search/?api=1&query=Google&query_place_id={data[i]['place_id']}"
        else:
            location_url = f"https://www.google.com/maps/search/?api=1&query={data[i]['lat']},{data[i]['lon']}"

        temp_H = H.copy()
        # 設定停留區間
        if i == 0:
            temp_H["text"] = data[i]['start_time']
        elif i == len(data) - 1:
            temp_H["text"] = " " + data[i]['end_time']
        else:
            temp_H["text"] = " " + \
                '-'.join([data[i]['start_time'], data[i]['end_time']])

        # 顯示下一個目的地的交通資訊
        transport_info = {
            "type": "box",
            "layout": "horizontal",
            "contents": [],
            "height": "0px"
        }

        # 如果不是最後一個地點，顯示到下一個地點的交通資訊
        if i < len(data) - 1:
            next_point = data[i + 1]
            transport_icon = transport_icons.get(
                next_point['transport']['mode'], "🚗")
            transport_time = next_point['transport'].get('time', '15')
            transport_info = {
                "type": "box",
                "layout": "horizontal",
                "contents": [
                    {
                        "type": "text",
                        "text": f"↓ {transport_icon} {transport_time}分鐘 ↓",
                        "size": "xs",
                        "color": "#888888",
                        "flex": 5
                    }
                ],
                "margin": "sm"
            }

        location_container = {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "box",
                    "layout": "horizontal",
                    "spacing": "lg",
                    "contents": [
                        temp_H,
                        {
                            "type": "text",
                            "text": data[i]["name"],
                            "size": "sm",
                            "spacing": "md",
                            "align": "start",
                            "wrap": True,
                            "flex": 3,
                            "maxLines": 2,
                            "weight": "regular",
                            "color": "#555555",
                            "action": {
                                "type": "uri",
                                "uri": location_url
                            }
                        },
                        {
                            "type": "text",
                            "text": "×",
                            "size": "md",
                            "color": "#FF6B6B",
                            "align": "center",
                            "action": {
                                "type": "postback",
                                "label": " ",
                                "data": f"cancel_{plan_index}_{data[i]['step']}_{data[i]['name']}_{data[i]['label']}"
                            },
                            "flex": 0,
                            "weight": "bold"
                        }
                    ]
                },
                transport_info
            ],
            "paddingAll": "sm",
            "backgroundColor": "#FFFFFF",
            "cornerRadius": "lg",
            "borderWidth": "none"
        }

        contents.append(location_container)

    First_bubble = {
        "type": "bubble",
        "body": {
            "type": "box",
            "layout": "vertical",
            "spacing": "md",
            "backgroundColor": "#F8F9FA",
            "paddingAll": "xl",
            "contents": [
                {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        {
                            "type": "text",
                            "text": "📍 一日遊行程",
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
        },
        "styles": {
            "body": {
                "backgroundColor": "#F8F9FA"
            }
        }
    }

    cot = {
        "type": "box",
        "layout": "vertical",
        "spacing": "sm",
        "margin": "md",
        "contents": contents
    }

    First_bubble['body']['contents'].append(cot)

    footer = {
        "type": "box",
        "layout": "horizontal",
        "spacing": "md",
        "margin": "none",
        "contents": [
            {
                "type": "button",
                "style": "primary",
                "action": {
                    "type": "postback",
                    "label": "收藏行程",
                    "data": "save_schedule"
                },
                "color": "#FF8DA1",
                "flex": 1,
                "height": "sm"
            },
            {
                "type": "button",
                "style": "primary",
                "action": {
                    "type": "uri",
                    "label": "地圖網址",
                    "uri": "https://www.google.com/maps"
                },
                "color": "#5C7AEA",
                "flex": 1,
                "height": "sm"
            }
        ],
        "paddingAll": "lg",
        "backgroundColor": "#F8F9FA"
    }

    First_bubble['footer'] = footer

    return First_bubble


def dir_uri(data):
    directions_url = "https://www.google.com/maps/dir/?api=1"

    # 設定交通方式 (假設所有路段都用同一種交通方式)
    if data:
        directions_url += f"&travelmode={data[0]['transport']['mode_eng']}"

    # 設定起點 (origin) - 使用第一個地點
    if data:
        # 或使用 place_id: f"&origin=place_id:{data[0]['place_id']}"
        directions_url += f"&origin={data[0]['name']}({data[0]['lat']},{data[0]['lon']})"

    # 初始化 waypoints 列表
    waypoints = []

    # 迴圈處理途經點 (waypoints) - 從第二個點到倒數第二個點
    if len(data) > 2:  # 至少要有三個地點才能有途經點
        for i in range(1, len(data) - 1):  # 從索引 1 到 倒數第二個索引
            # 或使用經緯度: waypoints.append(f"{data[i]['lat']},{data[i]['lon']}")
            waypoints.append(f"{data[i]['name']}({data[i]['lat']},{data[i]['lon']})")

    # 組裝 waypoints 字串 (使用 "|" 連接，避免最後多一個 "|")
    if waypoints:
        directions_url += "&waypoints=" + "|".join(waypoints)

    # 設定終點 (destination) - 使用最後一個地點 (在 waypoints 設定之後)
    if len(data) > 1:  # 至少要有兩個地點才能設定終點
        # 或使用 place_id: f"&destination=place_id:{data[-1]['place_id']}"
        directions_url += f"&destination={data[-1]['name']}({data[-1]['lat']},{data[-1]['lon']})"

    print(directions_url)  # 印出最終的 URL 方便檢查
    return directions_url
