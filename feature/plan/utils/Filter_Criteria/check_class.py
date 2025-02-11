def filter_by_label_type(points, desired_label:str):
    """
    根據指定的 label_type 篩選  一般商店
                                小吃
                                日用品商店
                                休閒設施
                                伴手禮商店
                                室內旅遊景點
                                室外旅遊景點
                                甜品店/飲料店
                                餐廳
                                購物商場
                                文化/歷史景點
                                自然景點
                                咖啡廳
                                一般商店
    
    :restaurants: 地點列表，每個地點包含 placeID 和 label_type  。 珣那包
    :desired_label: '餐廳'|'咖啡廳'|'小吃'|'景點'               。pon那包
    :return: 符合條件的 placeID 列表。
    """

    label_mapping = {
        '餐廳': ['餐廳', '咖啡廳', '小吃'],
        '咖啡廳': ['咖啡廳', '甜品店/飲料店'],
        '小吃': ['小吃', '甜品店/飲料店'],
        '景點': [
            '一般商店',
            '日用品商店',
            '休閒設施',
            '伴手禮商店',
            '室內旅遊景點',
            '室外旅遊景點',
            '購物商場',
            '文化/歷史景點',
            '自然景點',
            '一般商店',
        ],
    }


    matching_places = []
    for points in points:
        
        label = points.get("new_label_type")
        label_required = label_mapping[desired_label]
        if label in label_required:
            matching_places.append(points['placeID'])
    return matching_places


if __name__ == "__main__":
    # 測試數據
    points = [
        {"placeID": 1, "new_label_type": "小吃"},
        {"placeID": 2, "new_label_type": "小吃"},
        {"placeID": 3, "new_label_type": "伴手禮商店"},
        {"placeID": 4, "new_label_type": "購物商場"},
        {"placeID": 5, "new_label_type": "小吃"},
        {"placeID": 6, "new_label_type": "自然景點"},
        {"placeID": 7, "new_label_type": "小吃"},
        {"placeID": 8, "new_label_type": "餐廳"}
    ]
    user_requirements = [
        {
            "星期別": 1,
            "時間": "10:00",
            "類別": "景點",
            "預算": 500,
            "出發地": (25.0478, 121.5171),
            "可接受距離門檻(KM)": 10,
            "交通類別": "步行"
        }]
    # 使用者輸入
    user_input = user_requirements[0].get("類別")

    # 篩選符合條件的地點
    matching_places = filter_by_label_type(points, user_input)
    placeID = matching_places
    # 輸出結果
    print(f"符合 '{user_input}' 的地點 placeID:", placeID)
