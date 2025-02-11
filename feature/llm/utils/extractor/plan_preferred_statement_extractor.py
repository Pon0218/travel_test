def plan_preferred_statement_extractor(preferred_statement:list, limit:int, debuger: bool=False) -> list[str]:
    '''
    確保字數大於一定字數
    Args : 
        preferred_statement : ['喜歡探索文青風格的地方']
        limit : 字數門檻值
    return :
        ['喜歡探索文青風格的地方']
    '''
    default_statement = '喜歡探索文青風格的地方,喜歡尋找便宜又美味的午餐選擇,喜歡探訪獨特景點,並享受與朋友聚餐的晚餐時光'
    extract_preferred_statement = ['']
    try : 
        if len(preferred_statement[0]) > limit:
            extract_preferred_statement = [preferred_statement[0]]
            print(f'O : 情境搜索偏好句子 LLM 經過認證，格式無誤，超過 Limit : {limit} 個字')
        else:
            extract_preferred_statement = [default_statement]
            print(f'X : 情境搜索偏好句子 LLM 錯誤，小於 Limit : {limit} 個字，使用預設字串')
    except:
        print('X : 情境搜索偏好句子 LLM 格式錯誤 使用預設字串')
        extract_preferred_statement[0] = default_statement


    if debuger == True:
        print(extract_preferred_statement)

    return extract_preferred_statement



if __name__ == "__main__":
    test_cases = [
        (["短句"], 10),  # 少於 10 字，應該回傳 default_statement
        (["這是一個超過十個字的測試句子"], 10),  # 超過 15 字，應該回傳原本的字串
        ([""], 10),  # 空字串，應該回傳 default_statement
        (123, 10),   # 錯誤格式
    ]

    for preferred, limit in test_cases:
        print()
        plan_preferred_statement_extractor(preferred, limit, debuger=True)