import pytest
import os
from dotenv import load_dotenv

from feature.llm.LLM import LLM_Manager


@pytest.fixture
def llm_client():
    """準備 LLM 客戶端"""
    load_dotenv()
    api_key = os.getenv('ChatGPT_api_key')
    assert api_key is not None, "ChatGPT API key 未設置"
    return LLM_Manager(api_key)


@pytest.fixture
def test_inputs():
    """準備測試輸入"""
    return [
        "文青咖啡廳 1/14上午9點出發晚上8點回家",
        # 可以添加更多測試案例
    ]


def test_thinking_function(llm_client, test_inputs):
    """測試 Thinking_fun 函數"""
    for user_input in test_inputs:
        try:
            # 執行函數
            result_a, result_b, result_c = llm_client.Thinking_fun(user_input)

            # 基本檢查
            assert result_a is not None, "結果 A 不應為空"
            assert result_b is not None, "結果 B 不應為空"
            assert result_c is not None, "結果 C 不應為空"

            # 輸出結果以供檢視
            print(f"\n測試輸入: {user_input}")
            print(f"結果 A: {result_a}")
            print(f"結果 B: {result_b}")
            print(f"結果 C: {result_c}")

            # 修改過的類型檢查，包含 list 類型
            assert isinstance(result_a, (str, dict, list)), "結果 A 應該是字串、字典或列表"
            assert isinstance(result_b, (str, dict, list)), "結果 B 應該是字串、字典或列表"
            assert isinstance(result_c, (str, dict, list)), "結果 C 應該是字串、字典或列表"

        except Exception as e:
            pytest.fail(f"測試失敗，錯誤訊息：{str(e)}")


def test_api_response_time(llm_client):
    """測試 API 響應時間"""
    import time

    user_input = "文青咖啡廳 1/14上午9點出發晚上8點回家"
    start_time = time.time()

    try:
        result_a, result_b, result_c = llm_client.Thinking_fun(user_input)
        execution_time = time.time() - start_time

        print(f"\nAPI 響應時間: {execution_time:.2f} 秒")
        assert execution_time < 30, "API 響應時間過長"

    except Exception as e:
        pytest.fail(f"API 測試失敗：{str(e)}")


if __name__ == "__main__":
    pytest.main(["-v", "-s", __file__])
