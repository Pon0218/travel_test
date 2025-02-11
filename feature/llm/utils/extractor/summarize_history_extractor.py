def summarize_history_extractor(history:str, limit:int, debuger: bool=False) -> str:
    '''
    確保  history 值格式正確無誤，為 list, length=1, 內容為一個字串, 字數大於 limit
    '''
    extract_history_summarize = ['']
    try:
        if isinstance(history, list) and len(history) == 1 and isinstance(history[0], str) and len(history[0]) > limit:
            extract_history_summarize = history
            print(f'O :  history 值LLM 經過認證，格式正確無誤 ，為 list, length=1, 內容為一個字串, 字數大於 {limit}')
        else:
            print("X : history 值LLM 錯誤， 使用預設值 ['']")
    except :    # 基本上這個不會用到，上面已經排除完全錯誤，但還是多一層保護留著
        print('X : history 值LLM 格式錯誤， 使用預設值 ['']')
    
    if debuger == True:
        print(extract_history_summarize)
    
    return extract_history_summarize

if __name__ == '__main__':
    test_cases = [
        ["這是一段超過 10 個字的測試文本"],  # ✅ 符合條件的 `list`，長度超過 `limit`
        [],  # ❌ 空列表
        ["短句"],  # ❌ 字數小於 limit
        "這不是列表",  # ❌ 字串，不是列表
        ["這是一段符合條件的文字", "但這有兩個元素"],  # ❌ 列表內超過 1 個元素
        [1234567890],  # ❌ 數字，不是字串
        [[["巢狀列表"]]],  # ❌ 巢狀列表
        None,  # ❌ None 不是列表
    ]

    for test_history in test_cases:
        print()
        summarize_history_extractor(test_history, limit=10, debuger=True)