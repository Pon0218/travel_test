from feature.llm.LLM import LLM_Manager
from feature.retrieval.qdrant_search import qdrant_search
from feature.retrieval.utils import jina_embedding, json2txt, qdrant_control
from feature.plan.Contextual_Search_Main import filter_and_calculate_scores
from feature.sql_csv import sql_csv
from typing import Dict, List, Tuple, Any

def rerun_rec(query_info: Dict[str, Any], config: Dict[str, str]) -> List[Dict[str, Any]]:
    """
    根據已有的查詢信息重新執行推薦
    
    參數:
        query_info: 從 MongoDB 獲取的用戶查詢信息字典
        config: 配置信息
        
    返回:
        List[Dict[str, Any]]: 推薦的地點列表
    """
    weights = {'distance': 0.2, 'comments': 0.4, 'similarity': 0.4}
    print("1. MongoDB black_list:", query_info["black_list"])
    # 向量搜索，直接在此階段使用黑名單過濾
    qdrant_obj = qdrant_search(
        collection_name='view_restaurant',
        config=config,
        score_threshold=0.6,
        limit=1000,
        black_list=list(query_info["black_list"])  # 將 set 轉換為 list
    )
    vector_results = qdrant_obj.cloud_search(query_info["query_of_llm"])
    
    # SQL過濾
    sql_results = sql_csv.pandas_search(
        system='plan',
        system_input=vector_results,
        special_request_list=query_info["special_requirement"]
    )
    
    # 最終過濾和評分
    final_results = filter_and_calculate_scores(
        sql_results,
        query_info["user_requirement"],
        weights
    )

    print("重跑成功")
    return final_results

if __name__ == "__main__":
    from pprint import pprint
    from dotenv import dotenv_values
    from feature.nosql_mongo.mongo_rec.mongoDB_ctrl_disat import MongoDBManage_unsatisfied
    
    # 載入 .env 檔案中的環境變數
    config = dotenv_values("./.env")
    if len(config) == 0:
        print('請檢查 .env 路徑')
    
    # 初始化 MongoDB 並獲取用戶記錄
    mongodb_obj = MongoDBManage_unsatisfied(config)
    query_info = mongodb_obj.get_user_records("U123456789")[0]  # 假設取第一條記錄
    mongodb_obj.close()
    
    # 使用獲取的記錄執行推薦
    results = rerun_rec(query_info, config)
    print("重新推薦結果：")
    pprint(results, sort_dicts=False)