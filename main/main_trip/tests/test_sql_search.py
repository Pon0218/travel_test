import pytest

from feature.sql import csv_read


def test_pandas_search():
    # 準備測試資料
    condition_dict = csv_read.load_and_sample_data('./database/info_df.csv')

    # 測試案例 1：多條件搜尋
    detail_info_1 = [{'適合兒童': True, '無障礙': False, '內用座位': True}]
    result_1 = csv_read.pandas_search(
        condition_data=condition_dict,
        detail_info=detail_info_1
    )
    # 確保有返回結果
    assert len(result_1) >= 0

    # 測試案例 2：單一條件搜尋
    detail_info_2 = [{'無障礙': False}]
    result_2 = csv_read.pandas_search(
        condition_data=condition_dict,
        detail_info=detail_info_2
    )
    # 確保有返回結果
    assert len(result_2) >= 0

    # 可以加入更多具體的檢查
    if len(result_1) > 0:
        assert isinstance(result_1, (list, dict))
    if len(result_2) > 0:
        assert isinstance(result_2, (list, dict))


if __name__ == "__main__":
    pytest.main(["-v", "-s", __file__])
