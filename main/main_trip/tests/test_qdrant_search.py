import pytest
from dotenv import load_dotenv
import os

from feature.retrieval.qdrant_search import qdrant_search


@pytest.fixture
def config():
    """準備測試環境配置"""
    load_dotenv()
    return {
        'jina_url': os.getenv('jina_url'),
        'jina_headers_Authorization': os.getenv('jina_headers_Authorization'),
        'qdrant_url': os.getenv('qdrant_url'),
        'qdrant_api_key': os.getenv('qdrant_api_key')
    }


@pytest.fixture
def qdrant_client(config):
    """建立 qdrant 客戶端"""
    return qdrant_search(
        collection_name='view_restaurant_test',
        config=config,
        score_threshold=0.5,
        limit=30
    )


def test_qdrant_search_cafe(qdrant_client):
    """測試咖啡廳搜尋"""
    input_query = {'上午': '喜歡在文青咖啡廳裡享受幽靜且美麗的裝潢'}
    result = qdrant_client.trip_search(input_query)

    # 基本檢查
    assert result is not None
    assert isinstance(result, (list, dict))
    # 如果知道預期的結果格式，可以加入更具體的檢查


def test_qdrant_search_restaurant(qdrant_client):
    """測試餐廳搜尋"""
    input_query = {'中餐': '好吃很辣便宜加飯附湯環境整潔很多人可以停車'}
    result = qdrant_client.trip_search(input_query)

    # 基本檢查
    assert result is not None
    assert isinstance(result, (list, dict))


def test_environment_variables(config):
    """測試環境變數是否都有正確設置"""
    required_vars = ['jina_url', 'jina_headers_Authorization',
                     'qdrant_url', 'qdrant_api_key']
    for var in required_vars:
        assert config[var] is not None, f"Missing environment variable: {var}"


if __name__ == "__main__":
    pytest.main(["-v", "-s", __file__])
