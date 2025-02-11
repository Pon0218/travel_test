from feature.llm.utils.extractor.format_valid.format_valid import (
    is_valid_24_hour_time, 
    is_float, 
    is_valid_lat_lon, 
    is_valid_one_to_seven,
)

def plan_basic_req_extractor(basic_req:list[dict], debuger: bool=False):
    '''
    重新提取 情境搜索的 LLM 輸出，確保格式無誤
    '''
    try:
        basic_req = basic_req[0]
        extract_basic_req = [{
            # 若無則給 'none'
            '星期別': basic_req['星期別'] if is_valid_one_to_seven(basic_req['星期別']) else 'none',  
            '時間': str(basic_req['時間']) if is_valid_24_hour_time(basic_req['時間']) else 'none',   
            '類別': str(basic_req['類別']) if basic_req['交通方式'] in ['餐廳','咖啡廳','小吃','景點'] else 'none', 
            '預算': basic_req['預算'] if is_float(basic_req['預算']) else 'none', 

            # 若無則給 預設值
            '出發地點': basic_req['出發地點'] if is_valid_lat_lon(basic_req['出發地點']) else (25.0418, 121.5654),
            '可接受距離門檻(KM)': basic_req['可接受距離門檻(KM)'] if is_float(basic_req['可接受距離門檻(KM)']) else 30,   
            '交通方式': str(basic_req['交通方式']) if basic_req['交通方式'] in ['大眾運輸','開車','騎自行車','步行'] else '大眾運輸', 
        }]
        print('O : 客戶基本要求llm 經過認證，格式無誤')
    except:
        print('X : 客戶基本要求llm 錯誤, 客戶基本要求使用預設值')
        extract_basic_req = [{
        # 'none'
        '星期別': 'none',  
        '時間': 'none',   
        '類別': 'none', 
        '預算': 'none', 

        # 預設值
        '出發地點': (25.0418, 121.5654), # 台北101經緯度
        '可接受距離門檻(KM)': 30,   
        '交通方式': '大眾運輸',
        }]

        
    
    if debuger == True:
        from pprint import pprint
        pprint(extract_basic_req, sort_dicts=False)

    return extract_basic_req

if __name__ == '__main__':
    basic_req = [{
        '星期別': 'none',   # 1-7|'none'
        '時間': 'none',     # '00:00'|'none'
        '類別': 'none',     # '餐廳'|'咖啡廳'|'小吃'|'景點'|'none'
        '預算': 'none',     # float|'none'
        '出發地點': 'none', # 經緯度數值|(25.0418, 121.5654) 台北101經緯度
        '可接受距離門檻(KM)': 'none',   # float|30
        '交通方式': 'none'  # "大眾運輸"|"開車"|"騎自行車"|"步行"
    }]

    # basic_req = ''

    plan_basic_req_extractor(basic_req, debuger=True)