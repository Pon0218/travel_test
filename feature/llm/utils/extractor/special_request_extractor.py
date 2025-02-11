def special_request_extractor(special_list: list[dict], debuger: bool=False):
    '''
    Args :
        special_list : llm 經過 json load 出的東西
        debuger : 當其為 True 時會 print 出檔案

    return :
        extract_special_list : 重新提取後的確認無誤的 special_list
    ---
    將特殊要求由提取器重新提出，確保 llm 生成格式正確

    !!! 若遇到內容錯誤格式，則直接輸出 False 不進行該項特殊需求篩選

    !!! 若遇到格式錯誤 則回傳全部 False 資料並印出特殊篩選llm 錯誤不進行特殊篩選
    '''
    try : 
        special_list = special_list[0]
        extract_special_list = [{
            '內用座位': special_list['內用座位'] if isinstance(special_list['內用座位'], bool) else False,
            '洗手間': special_list['洗手間'] if isinstance(special_list['洗手間'], bool) else False,
            '適合兒童': special_list['適合兒童'] if isinstance(special_list['適合兒童'], bool) else False,
            '適合團體': special_list['適合團體'] if isinstance(special_list['適合團體'], bool) else False,
            '現金': special_list['現金'] if isinstance(special_list['現金'], bool) else False,
            '其他支付': special_list['其他支付'] if isinstance(special_list['其他支付'], bool) else False,
            '收費停車': special_list['收費停車'] if isinstance(special_list['收費停車'], bool) else False,
            '免費停車': special_list['免費停車'] if isinstance(special_list['免費停車'], bool) else False,
            'wi-fi': special_list['wi-fi'] if isinstance(special_list['wi-fi'], bool) else False,
            '無障礙': special_list['無障礙'] if isinstance(special_list['無障礙'], bool) else False,
        }]
        print('O : 客戶特殊需求llm 經過認證，格式無誤')
    except :
        print('X : 特殊篩選llm 錯誤不進行特殊篩選')
        extract_special_list = [{
            '內用座位': False,
            '洗手間': False,
            '適合兒童': False,
            '適合團體': False,
            '現金': False,
            '其他支付': False,
            '收費停車': False,
            '免費停車': False,
            'wi-fi': False,
            '無障礙': False
        }]
        
    
    if debuger == True:
        print(extract_special_list)

    return extract_special_list




if __name__ == '__main__':
    special_list = [{
        # True 測試
        '內用座位': True,
        '洗手間': True,

        # False 測試
        '適合兒童': False,
        '適合團體': False,
        '現金': False,
        '其他支付': False,
        '收費停車': False,
        '免費停車': False,

        # 錯誤測試
        'wi-fi': 123,
        '無障礙': 'abcde',
    }]

    # special_list 格式錯誤測試
    # special_list = '格式錯誤測試'

    special_request_extractor(special_list, debuger=True)