import pytest
from unittest.mock import patch, MagicMock
from typing import Union, List

from feature.llm.LLM import LLM_Manager


@pytest.fixture
def mock_llm():
    """建立測試用的LLM物件"""
    return LLM_Manager("test_api_key")


def create_mock_response(content: str) -> dict:
    """建立模擬的OpenAI API回應

    Args:
        content: API要回傳的內容字串

    Returns:
        dict: 模擬的API回應格式
    """
    return {
        'choices': [{
            'message': {
                'content': content.strip()
            }
        }]
    }


@pytest.mark.parametrize(
    "api_response,expected",
    [
        ("0", 0),  # 完全重新規劃
        ("5", 5),  # 從第5個點重新規劃
        ("[1, 3, 5]", [1, 3, 5]),  # 多個重啟點
    ]
)
def test_restart_index_type(mock_llm, api_response: str, expected: Union[int, List[int]]):
    """測試restart_index回傳值的類型

    Args:
        mock_llm: LLM物件的fixture
        api_response: 模擬的API回應內容
        expected: 預期的輸出結果
    """
    # 模擬OpenAI API回應
    with patch('openai.ChatCompletion.create') as mock_chat:
        mock_chat.return_value = create_mock_response(api_response)

        # 執行測試
        result = mock_llm.Thinking_fun("測試輸入")

        # 檢查restart_index (在result的第3個位置)
        restart_index = result[3]

        # 驗證型別和值
        assert isinstance(restart_index, type(expected))
        assert restart_index == expected


@pytest.mark.parametrize(
    "api_response,expected_error",
    [
        ("", ValueError),  # 空值
        ("abc", ValueError),  # 非數字字串
        ("-1", ValueError),  # 負數
        ("[1, -2, 3]", ValueError),  # 含負數的列表
        ("1.5", ValueError),  # 浮點數
    ]
)
def test_restart_index_invalid_input(mock_llm, api_response: str, expected_error: Exception):
    """測試無效輸入的處理

    Args:
        mock_llm: LLM物件的fixture
        api_response: 模擬的無效API回應
        expected_error: 預期會拋出的異常類型
    """
    with patch('openai.ChatCompletion.create') as mock_chat:
        mock_chat.return_value = create_mock_response(api_response)

        # 檢查是否拋出預期的異常
        with pytest.raises(expected_error):
            mock_llm.Thinking_fun("測試輸入")


def test_restart_index_concurrent_calls(mock_llm):
    """測試同時呼叫API的情況 

    Args:
        mock_llm: LLM物件的fixture
    """
    with patch('openai.ChatCompletion.create') as mock_chat:
        # 模擬不同的API回應
        responses = [
            create_mock_response("0"),
            create_mock_response("5"),
            create_mock_response("[1, 2, 3]")
        ]
        mock_chat.side_effect = responses

        # 同時呼叫多次
        results = []
        for _ in range(3):
            result = mock_llm.Thinking_fun("測試輸入")
            results.append(result[3])  # 取得restart_index

        # 驗證結果
        assert results[0] == 0
        assert results[1] == 5
        assert results[2] == [1, 2, 3]


def test_restart_index_api_error(mock_llm):
    """測試API錯誤的處理 

    Args:
        mock_llm: LLM物件的fixture
    """
    with patch('openai.ChatCompletion.create') as mock_chat:
        # 模擬API異常
        mock_chat.side_effect = Exception("API錯誤")

        # 確認異常有被正確拋出
        with pytest.raises(Exception) as exc_info:
            mock_llm.Thinking_fun("測試輸入")

        assert "API錯誤" in str(exc_info.value)


if __name__ == "__main__":
    pytest.main(["-v", "-s", __file__])
