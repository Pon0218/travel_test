import pytest
from dotenv import load_dotenv
import os
import time
from concurrent.futures import ThreadPoolExecutor

from feature.retrieval.qdrant_search import qdrant_search


@pytest.fixture
def test_queries():
    """準備測試查詢資料"""
    return [
        {'上午': '喜歡在文青咖啡廳裡享受幽靜且美麗的裝潢'},
        {'中餐': '好吃很辣便宜加飯附湯環境整潔很多人可以停車'},
        {'下午': '充滿歷史感的日式建築'},
        {'晚餐': '適合多人聚餐的餐廳'},
        {'晚上': '可以看夜景的地方'}
    ]


@pytest.fixture
def qdrant_client():
    """準備 qdrant 客戶端"""
    load_dotenv()
    config = {
        'jina_url': os.getenv('jina_url'),
        'jina_headers_Authorization': os.getenv('jina_headers_Authorization'),
        'qdrant_url': os.getenv('qdrant_url'),
        'qdrant_api_key': os.getenv('qdrant_api_key')
    }
    return qdrant_search(
        collection_name='view_restaurant_test',
        config=config
    )


def test_single_search(qdrant_client, test_queries):
    """測試單一搜尋功能"""
    single_results = {}
    start_time = time.time()

    for query in test_queries:
        result = qdrant_client.trip_search(query)
        single_results.update(result)

    execution_time = time.time() - start_time
    print(f"\n單一搜尋執行時間: {execution_time:.2f} 秒")

    # 驗證結果
    assert single_results, "搜尋結果不應為空"
    for period, ids in single_results.items():
        assert isinstance(ids, list), f"{period} 的結果應該是列表"


def test_parallel_search(qdrant_client, test_queries):
    """測試平行搜尋功能"""
    parallel_results = {}
    start_time = time.time()

    with ThreadPoolExecutor() as executor:
        future_to_query = {
            executor.submit(qdrant_client.trip_search, query): query
            for query in test_queries
        }
        for future in future_to_query:
            try:
                result = future.result()
                parallel_results.update(result)
            except Exception as e:
                pytest.fail(f"平行搜尋發生錯誤: {str(e)}")

    execution_time = time.time() - start_time
    print(f"\n平行搜尋執行時間: {execution_time:.2f} 秒")

    # 驗證結果
    assert parallel_results, "搜尋結果不應為空"
    for period, ids in parallel_results.items():
        assert isinstance(ids, list), f"{period} 的結果應該是列表"


def test_search_results_quality(qdrant_client, test_queries):
    """測試搜尋結果品質"""
    for query in test_queries:
        result = qdrant_client.trip_search(query)

        # 基本驗證
        assert result, f"查詢 {query} 應該要有結果"

        for period, ids in result.items():
            # 檢查結果格式
            assert isinstance(ids, list), f"{period} 的結果應該是列表"
            # 檢查是否有結果
            assert len(ids) > 0, f"{period} 應該要有至少一個結果"
            # 檢查前三個結果
            if len(ids) >= 3:
                print(f"\n{period} 前三個結果: {ids[:3]}")


def test_performance_comparison(qdrant_client, test_queries):
    """比較單一搜尋和平行搜尋的性能"""
    # 單一搜尋
    start_time = time.time()
    single_results = {}
    for query in test_queries:
        result = qdrant_client.trip_search(query)
        single_results.update(result)
    single_time = time.time() - start_time

    # 平行搜尋
    start_time = time.time()
    parallel_results = {}
    with ThreadPoolExecutor() as executor:
        future_to_query = {
            executor.submit(qdrant_client.trip_search, query): query
            for query in test_queries
        }
        for future in future_to_query:
            result = future.result()
            parallel_results.update(result)
    parallel_time = time.time() - start_time

    # 輸出性能比較
    print(f"\n性能比較:")
    print(f"單一搜尋時間: {single_time:.2f} 秒")
    print(f"平行搜尋時間: {parallel_time:.2f} 秒")
    print(f"時間差異: {single_time - parallel_time:.2f} 秒")

    # 驗證兩種方法的結果是否一致
    assert set(single_results.keys()) == set(
        parallel_results.keys()), "兩種方法的結果應該要有相同的時段"


if __name__ == "__main__":
    pytest.main(["-v", "-s", __file__])
