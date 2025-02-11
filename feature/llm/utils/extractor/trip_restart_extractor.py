def trip_restart_extractor(restart:list[int], debuger: bool=False) -> list[int]:
    '''
    確保  LLM restart 值格式正確無誤，為 [int], length=1
    '''
    extract_restart = [0]
    try:
        if isinstance(restart, list) and len(restart) == 1 and isinstance(restart[0], int):
            extract_restart = restart
            print('O : LLM restart 值格式正確無誤，為 [int], length=1')
        else:
            print("X : LLM restart 不符合為list 或 list內不只一個 或 list內非int, 使用預設值")
    except :
        print('X : LLM restart 格式錯誤，使用預設值 [0]')
    
    if debuger == True:
        print(extract_restart)
    
    return extract_restart


if __name__ == '__main__':
    test_cases = [
        [2],         # ✅ 單一整數
        [],          # ❌ 空列表
        [2, 3],      # ❌ 超過一個元素
        ["2"],       # ❌ 字串，不是整數
        [2.5],       # ❌ 浮點數，不是整數
        [[2]],       # ❌ 巢狀列表
        {"a": 2},    # ❌ 字典，不是列表
        (2,),        # ❌ Tuple，不是列表
        None,        # ❌ None 不是列表
    ]

    for test_restart in test_cases:
        print()
        trip_restart_extractor(test_restart, debuger=True)
