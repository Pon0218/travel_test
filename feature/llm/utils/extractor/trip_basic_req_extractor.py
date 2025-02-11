from feature.llm.utils.extractor.format_valid.format_valid import (
    is_valid_24_hour_time, 
    is_float, 
    is_valid_mm_dd,
)

def trip_basic_req_extractor(basic_req:list[dict], debuger: bool=False):
    '''
    重新提取旅遊 LLM 輸出, 除了 出發地點、結束地點只能確認是字串格式外 ], 確保LLM格式無誤
    '''
    basic_req = basic_req[0]
    try:
        extract_basic_req = [{
            '出發時間': str(basic_req['出發時間']) if is_valid_24_hour_time(basic_req['出發時間']) else '09:00',
            '結束時間': str(basic_req['結束時間']) if is_valid_24_hour_time(basic_req['結束時間']) else '21:00',
            '出發地點': str(basic_req['出發地點']), # 只能確定是字串
            '結束地點': str(basic_req['結束地點']), # 只能確定是字串
            '交通方式': basic_req['交通方式'] if basic_req['交通方式'] in ['大眾運輸','開車','騎車','步行'] else '大眾運輸',
            '可接受距離門檻(KM)': basic_req['可接受距離門檻(KM)'] if is_float(basic_req['可接受距離門檻(KM)']) else 30,
            '早餐時間': str(basic_req['早餐時間']) if is_valid_24_hour_time(basic_req['早餐時間']) else 'none',
            '中餐時間': str(basic_req['中餐時間']) if is_valid_24_hour_time(basic_req['中餐時間']) else '12:00',
            '晚餐時間': str(basic_req['晚餐時間']) if is_valid_24_hour_time(basic_req['晚餐時間']) else '18:00',
            '預算': basic_req['預算'] if is_float(basic_req['預算']) else 'none',
            '出發日': str(basic_req['出發日']) if is_valid_mm_dd(basic_req['出發日']) else 'none',
        }]
        print('O : 客戶基本要求llm 經過認證，其他格式無誤\n    ! 除了"出發地點"及"結束地點" ! ')
    except:
        # 預設值
        print('X : 客戶基本要llm 錯誤, 客戶基本要求使用預設值')
        extract_basic_req = [{
            '出發時間': '09:00',
            '結束時間': '21:00',
            '出發地點': '台北車站',
            '結束地點': 'none',
            '交通方式': '大眾運輸',
            '可接受距離門檻(KM)': 30,
            '早餐時間': 'none',
            '中餐時間': '12:00',
            '晚餐時間': '18:00',
            '預算': 'none',
            '出發日': 'none',
        }]


    if debuger == True :
        from pprint import pprint
        pprint(extract_basic_req, sort_dicts=False)

    return extract_basic_req


if __name__ == "__main__":
    basic_req = [{
        '出發時間': '00:00',         # '00:00'|'none'
        '結束時間': '21:00',         # '00:00'|'none'
        '出發地點': '台北車站',       # str|'none'          !! 要求一定要小地標
        '結束地點': 'none',          # str|'none'          !! 要求一定要小地標
        '交通方式': '大眾運輸',       # "大眾運輸" | "開車" | "騎車" | "步行"  !!  如果沒給就給 '大眾運輸'
        '可接受距離門檻(KM)': 30,     # int         !! 沒給就給 30
        '早餐時間': 'none',          # '00:00'|'none'
        '中餐時間': '12:00',         # '00:00'|'12:00'      !! 沒給則給 '12:00'
        '晚餐時間': '18:00',         # '00:00'|'18:00'      !! 沒給則給 '18:00'
        '預算': 'none',              #  int | "none"        !! 確保一定有 "none"
        '出發日': 'none'             # "mm-dd" | "none"     !! 確保一定有 "none"
    }]

    trip_basic_req_extractor(basic_req, debuger=True)

