from feature.llm.LLM import LLM_Manager
from feature.retrieval.qdrant_search import qdrant_search
from feature.plan.Contextual_Search_Main import filter_and_calculate_scores
from feature.sql_csv import sql_csv

def recommandation(user_Q: str, config: dict[str, str]) -> list[dict]:
    """
    處理用戶查詢並返回推薦結果以及查詢相關信息
    
    Args:
        user_Q: 用戶的查詢字串
        config: 配置信息
        
    Returns:
        Tuple[List[Dict], Dict]: 
            - 推薦的地點列表
            - 查詢相關信息(用於存儲到MongoDB)
    """
    # 初始化 LLM 物件
    LLM_obj = LLM_Manager(config['ChatGPT_api_key'])
    weights = {'distance': 0.2, 'comments': 0.3, 'similarity': 0.5}
    
    # 獲取 LLM 分析結果
    results = LLM_obj.Cloud_fun(user_Q)
    
    # 提取分析結果
    cloud_description = results[0]  # LLM解析資料:形容客戶行程的一句話
    special_requirements = results[1]  # LLM解析資料:確認是否具有特殊要求
    user_requirements = results[2]  # LLM解析資料:客戶基本要求資料
    
    # 向量搜索
    qdrant_obj = qdrant_search(
        collection_name='view_restaurant',
        config=config,
        score_threshold=0.6,
        limit=1000,
    )
    vector_results = qdrant_obj.cloud_search(cloud_description)
    
    # SQL過濾
    sql_results = sql_csv.pandas_search(
        system='plan',
        system_input=vector_results,
        special_request_list=special_requirements
    )
    
    # 最終過濾和評分
    final_results = filter_and_calculate_scores(
        sql_results,
        user_requirements,
        weights
    )
    
    # 準備MongoDB存儲用的資訊
    query_info = {
        "line_user_id": "",  # 預留給Line用戶ID
        "query": user_Q,  # 用戶輸入的搜索語句
        "query_of_llm": cloud_description,  # LLM分析的語句
        "special_requirement": special_requirements,  # 特殊需求字典
        "user_requirement": user_requirements,  # 用戶需求字典
        "black_list": set()  # 初始化空的黑名單集合
    }
    
    return final_results, query_info

if __name__ == "__main__":
    from pprint import pprint
    from dotenv import dotenv_values
    
    # 載入 .env 檔案中的環境變數
    config = dotenv_values("./.env")
    if len(config) == 0:
        print('please check .env path')
    
    results, query_info = recommandation("請推薦好吃台北餐廳", config)
    print("推薦結果：")
    pprint(results, sort_dicts=False)
    print("\n查詢資訊 :")
    pprint(query_info, sort_dicts=False)