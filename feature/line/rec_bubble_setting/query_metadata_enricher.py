from typing import Dict, Any, List


def enrich_query(
    query_info: Dict[str, Any],
    place_ids: List[str]
) -> Dict[str, Any]:
    """
    補充查詢資訊的元數據
    
    Args:
        query_info: 從 recommandation 函數獲得的原始查詢資訊
        place_ids: 不滿意的地點ID列表
        
    Returns:
        Dict[str, Any]: 補充完整的查詢資訊
    """
    try:
        # 複製原始查詢資訊以避免修改原始資料
        enriched_info = query_info.copy()
        
        # 將新的 place_ids 與原有的 black_list 合併
        original_black_list = set(enriched_info.get("black_list", set()))
        enriched_info["black_list"] = original_black_list | set(place_ids)
        
        return enriched_info
        
    except Exception as e:
        print(f"補充查詢元數據時發生錯誤: {e}")
        raise


if __name__ == "__main__":
    # 測試用例
    test_query_info = {
        "line_user_id": "",
        "query": "推薦台北咖啡廳",
        "query_of_llm": "用戶想找一間環境舒適的咖啡廳",
        "special_requirement": {
            "內用座位": True,
            "wi-fi": True
        },
        "user_requirement": {
            "類別": "咖啡廳",
            "預算": 500
        },
        "black_list": set()
    }
    
    test_line_user_id = "U123456789"
    test_place_ids = ["place1", "place2", "place3"]
    
    enriched_info = enrich_query(
        test_query_info,
        test_line_user_id,
        test_place_ids
    )
    print("Enriched query info:")
    print(f"Line User ID: {enriched_info['line_user_id']}")
    print(f"Black List: {enriched_info['black_list']}")