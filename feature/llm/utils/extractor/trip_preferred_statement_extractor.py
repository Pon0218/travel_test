def trip_preferred_statement_extractor(preferred_statements:list[dict], limit:int, debuger: bool=False) -> list[dict]:
    '''
    確保每句字數大於 limit 字數
    '''
    
    defaut_statements = [
        {'上午': '我想逛充滿文青氛圍的街道,探索各種獨特的小店和咖啡館,'},
        {'中餐': '我想吃美味又平價的小吃 !!!'}, 
        {'下午': '我想去充滿藝術氣息和特色景點,享受不同的文化'},
        {'晚餐': '晚上想去適合與朋友聚餐的餐廳,可以享受美食同時聊天交流,'},
        {'晚上': '晚上想去可以看夜景, 氣氛幽靜可以約會的地方, 放鬆一天的行程'}
    ]
    extract_preferred_statement = []
    valid_num = 0       # 通過的數量
    unvalid_num = 0     # 不通過使用預設的數量
    try:
        for idx, diction in enumerate(preferred_statements): 
            # preferred_statement = list(diction.values())[0]
            key, preferred_statement = next(iter(diction.items()))
            if len(preferred_statement) > limit:
                extract_preferred_statement.append({key : preferred_statement})
                valid_num += 1
            else:
                extract_preferred_statement.append(defaut_statements[idx])
                unvalid_num += 1
            
        if valid_num > 0 :
            print(f'O : 旅遊規劃偏好句子 "{valid_num}" 句通過 LLM 經過認證，格式無誤，超過 Limit: {limit} 個字')
        if unvalid_num > 0:
            print(f'X : 旅遊規劃偏好句子 "{unvalid_num}" 句不通過, LLM 錯誤，小於: Limit {limit} 個字，使用預設字串')
    except :
        print('X : 旅遊規劃偏好句子 llm 格式錯誤, 全部使用預設值')
        extract_preferred_statement = defaut_statements
    
    if debuger == True:
        from pprint import pprint
        pprint(extract_preferred_statement, sort_dicts=False)
    return extract_preferred_statement


if __name__ == "__main__":
    defaut_statements = [
        {'上午': '我想逛充滿文青氛圍的街道,探索各種獨特的小店和咖啡館,'},
        {'中餐': '我想吃美味又平價的小吃 !!!'}, 
        {'下午': '我想去充滿藝術氣息和特色景點,享受不同的文化'},
        {'晚餐': '晚上想去適合與朋友聚餐的餐廳,可以享受美食同時聊天交流,'},
        {'晚上': '晚上想去可以看夜景, 氣氛幽靜可以約會的地方, 放鬆一天的行程'}
    ]
    trip_preferred_statement_extractor(defaut_statements, limit=20, debuger=True)
