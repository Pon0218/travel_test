def generate_flex_messages(locations):
    """
    生成 Line Flex Message 氣泡訊息
    
    參數:
        locations (dict): 以 placeID 為鍵的地點資訊字典
        
    回傳:
        dict: Line Flex Message 格式的輪播訊息
    """
    bubbles = []
    
    for place_id, location in locations.items():
        # 使用預設圖片如果沒有提供圖片URL
        image_url = location.get('image_url', 'https://via.placeholder.com/408x306')
        
        bubble = {
            "type": "bubble",
            "hero": {
                "type": "image",
                "size": "full",
                "aspectRatio": "20:13",
                "aspectMode": "cover",
                "url": image_url
            },
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "text",
                        "text": location.get('name', ''),
                        "weight": "bold",
                        "size": "xl",
                        "wrap": True
                    },
                    {
                        "type": "box",
                        "layout": "baseline",
                        "margin": "md",
                        "contents": [
                            {
                                "type": "text",
                                "text": f"評分: {location.get('rating', '無評分')}",
                                "size": "sm",
                                "color": "#999999",
                                "margin": "md",
                                "wrap": True
                            }
                        ]
                    },
                    {
                        "type": "text",
                        "text": location.get('address', ''),
                        "size": "sm",
                        "color": "#999999",
                        "margin": "md",
                        "wrap": True
                    },
                    {
                        "type": "box",
                        "layout": "horizontal",
                        "margin": "md",
                        "spacing": "sm",
                        "contents": [
                            {
                                "type": "button",
                                "style": "secondary",
                                "action": {
                                    "type": "message",
                                    "label": "❤️ 收藏",
                                    "text": f"收藏店家:{location.get('name', '')}"
                                },
                                "flex": 1
                            },
                            {
                                "type": "button",
                                "style": "secondary",
                                "action": {
                                    "type": "message",
                                    "label": "🔃 再推薦",
                                    "text": "推薦其他店家"
                                },
                                "flex": 1
                            }
                        ]
                    }
                ]
            },
            "footer": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "button",
                        "style": "link",
                        "height": "sm",
                        "action": {
                            "type": "uri",
                            "label": "查看地圖",
                            "uri": location.get('location_url', '')
                        }
                    }
                ]
            }
        }
        bubbles.append(bubble)
    
    return {
        "type": "carousel",
        "contents": bubbles
    }