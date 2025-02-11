
def Fourth():
    rainfall = {
        "type": "text",
        "text": "降雨機率:",
        "size": "sm",
        "align": "start"
    }
    rainfall_por={
        "type": "text",
        "text": "65%",
        "size": "sm",
        "align": "end"
    }

    tem= {
        "type": "text",
        "text": "溫度:",
        "size": "sm",
        "align": "start"
    }
    temperature={
        "type": "text",
        "text": "14-18°C",
        "size": "sm",
        "align": "end"
    }

    humidity = {
        "type": "text",
        "text": "相對溼度:",
        "size": "sm",
        "align": "start"
    }
    humidity_pro={
        "type": "text",
        "text": "86%",
        "size": "sm",
        "align": "end"
    }

    # contents_minimum，將 rainfall, temperature, humidity 內容加入
    contents_minimum1 = {
        "type": "box",
        "layout": "horizontal",
        "spacing": "md",
        "contents": [rainfall,rainfall_por]
    }
    contents_minimum2 = {
        "type": "box",
        "layout": "horizontal",
        "spacing": "md",
        "contents": [tem,temperature]
    }
    contents_minimum3 = {
        "type": "box",
        "layout": "horizontal",
        "spacing": "md",
        "contents": [humidity,humidity_pro]
    }
    weather={
            "type": "text",
            "text": "天氣預報",
            "size": "md",
            "spacing": "md",
            "align": "start"
            }
    # 設置包含 contents_minimum 的 box
    cot = {
        "type": "box",
        "layout": "vertical",
        "spacing": "md",
        "contents": [weather,contents_minimum1,contents_minimum2,contents_minimum3]
    }

    # 定義 Fourth_bubble 結構
    Fourth_bubble = {
        "type": "bubble",
        "body": {
            "type": "box",
            "layout": "vertical",
            "spacing": "lg",
            "contents": [
                {
                    "type": "text",
                    "text": "Travel recommendations",
                    "weight": "bold",
                    "color": "#1DB446",
                    "size": "sm"
                },
                {
                    "type": "text",
                    "text": "Taipei City",
                    "weight": "bold",
                    "size": "xxl",
                    "margin": "xs"
                },
                {
                    "type": "text",
                    "text": "Date: 2024/12/24",
                    "size": "sm",
                    "color": "#aaaaaa",
                    "wrap": True,
                    "margin": "md"
                },
                {
                    "type": "box",
                    "layout": "vertical",
                    "spacing": "md",
                    "contents": [
                        {
                            "type": "box",
                            "layout": "horizontal",
                            "spacing": "md",
                            "contents": [
                            ]
                        }
                    ]
                }
            ]
        }
    }

    # 把 cot 加入到 Fourth_bubble 的 contents 中
    Fourth_bubble['body']['contents'].append(cot)
    
    
    return Fourth_bubble

