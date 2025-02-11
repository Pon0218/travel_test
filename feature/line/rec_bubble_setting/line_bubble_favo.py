def generate_remove_flex_messages(locations, line_user_id):
    """
    生成用於移除收藏的 Line Flex Message 氣泡訊息
    
    參數:
        locations (dict): 以 placeID 為鍵的地點資訊字典
        line_user_id (str): Line 用戶識別碼
        
    回傳:
        tuple: (Line Flex Message 格式的輪播訊息, line_user_id)
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
                        "align": "center",
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
                                "align": "center",
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
                        "align": "center",
                        "wrap": True
                    },
                    {
                        "type": "box",
                        "layout": "vertical",
                        "margin": "md",
                        "contents": [
                            {
                                "type": "button",
                                "style": "secondary",
                                "action": {
                                    "type": "message",
                                    "label": "🗑️ 移除收藏",
                                    "text": f"移除{location.get('name', '')}"
                                }
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
    
    flex_message = {
        "type": "carousel",
        "contents": bubbles
    }
    
    return flex_message, line_user_id