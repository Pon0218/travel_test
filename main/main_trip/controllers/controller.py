import os
from dotenv import load_dotenv
from typing import Dict, List, Tuple
from concurrent.futures import ThreadPoolExecutor

import pandas as pd

from feature.llm.LLM import LLM_Manager
from feature.retrieval.qdrant_search import qdrant_search
from feature.sql_csv.sql_csv import pandas_search
from feature.nosql_mongo.mongo_trip.db_helper import trip_db
from feature.trip import TripPlanningSystem


class TripController:
    """行程規劃系統控制器"""

    def __init__(self, config: dict):
        """
        初始化控制器

        Args:
            config: dict (包含所需的所有設定)
                - jina_url: Jina AI 的 URL
                - jina_headers_Authorization: Jina 認證金鑰
                - qdrant_url: Qdrant 資料庫 URL
                - qdrant_api_key: Qdrant API 金鑰
                - ChatGPT_api_key: ChatGPT API 金鑰
        """
        self.config = config
        self.LLM_obj = LLM_Manager(self.config['ChatGPT_api_key'])
        self.trip_planner = TripPlanningSystem()

    def process_message(
        self,
        input_text: str = "",
        line_id: str = None,
    ) -> List[Dict]:
        """
        處理輸入訊息並返回結果

        Args:
            input_text: 使用者輸入文字
            line_id: user's line id (選填)

        Returns:
            str: 規劃好的行程或錯誤訊息
        """
        try:
            if line_id is None:
                line_id = "test_user_id"  # 這裡先寫死測試用

            # 1. 記錄用戶輸入
            # trip_db.record_user_input(line_id, input_text)

            # 2. 取得之前的行程
            latest = trip_db.get_latest_plan(line_id=line_id)
            latest_itinerary = latest.get('itinerary') if latest else None

            # 3. 準備給LLM的文字(包含歷史整理)
            input_for_LLM = self._prepare_input_text(
                text=input_text,
                line_id=line_id,
                previous_trip=latest_itinerary
            )

            # 4. LLM意圖分析
            period_describe, unique_requirement, base_requirement, restart_index = (
                self._analyze_intent(text=input_for_LLM)
            )

            if latest and 'restart_index' in latest:
                restart_index = latest.get('restart_index', 0)
            else:
                restart_index = int(restart_index[0]) if restart_index else 0

            # 5. 向量檢索
            placeIDs = self._vector_retrieval(period_describe)

            # 6. 取得景點詳細資料
            location_details = self._get_places(placeIDs, unique_requirement)
            location_details = self._add_duration(places=location_details)

            # 7. 規劃行程
            result = self._plan_trip(
                location_details=location_details,
                base_requirement=base_requirement,
                previous_trip=latest_itinerary,
                restart_index=restart_index,
            )

            # 8. 儲存規劃結果
            trip_db.save_plan(
                line_id=line_id,
                input_text=input_text,
                requirement=base_requirement,
                itinerary=result
            )

            return result

        except Exception as e:
            return f"抱歉，系統發生錯誤: {str(e)}"

    def _analyze_intent(
        self,
        text: str,
    ) -> Tuple[List[Dict], List[Dict], List[Dict], List[int]]:
        """
        分析使用者意圖

        Args:
            text (str): 使用者輸入

        Returns:
            Tuple[List[Dict], List[Dict], List[Dict[str, Union[int, str, None]]]]:
                - List[Dict]: 旅遊各時段形容詞 (對應圖中的 'a')
                - List[Dict]: 特殊需求 (對應圖中的 'b')
                - List[Dict[str, Union[int, str, None]]]: 客戶基本要求 (對應圖中的 'c')
        """
        return self.LLM_obj.Thinking_fun(text)

    def _vector_retrieval(self, period_describe: List[Dict]) -> Dict:
        """
        平行處理多個時段的向量搜尋

        Args:
            period_describe: List[Dict] 
                各時段的描述，例如：
                [
                    {'上午': '文青咖啡廳描述'},
                    {'中餐': '餐廳描述'}
                ]

        Returns:
            Dict: 各時段對應的景點ID
                {
                    '上午': ['id1', 'id2', ...],
                    '中餐': ['id3', 'id4', ...]
                }
        """
        try:
            # 建立 qdrant_search 實例
            qdrant_obj = qdrant_search(
                collection_name='view_restaurant',
                config=self.config,
                score_threshold=0.5,
                limit=100
            )
            # period_describe = [
            #     {'上午': '喜歡在文青咖啡廳裡享受幽靜且美麗的裝潢'},
            #     {'中餐': '好吃很辣便宜加飯附湯環境整潔很多人可以停車'},
            #     {'下午': '充滿歷史感的日式建築'},
            #     {'晚餐': '適合多人聚餐的餐廳'},
            #     {'晚上': '可以看夜景的地方'}
            # ]

            # 使用 ThreadPoolExecutor 進行平行處理
            results = {}
            with ThreadPoolExecutor() as executor:
                future_to_query = {
                    executor.submit(qdrant_obj.trip_search, query): query
                    for query in period_describe
                }

                for future in future_to_query:
                    try:
                        result = future.result()
                        results.update(result)
                    except Exception as e:
                        print(f"搜尋過程發生錯誤: {str(e)}")
                        continue

            return results

        except Exception as e:
            raise Exception(f"向量搜尋發生錯誤: {str(e)}")

    def _get_places(self, placeIDs: Dict, unique_requirement: List[Dict]) -> List[Dict]:
        """
        從資料庫取得景點詳細資料

        Args:
            placeIDs: Dict 
                各時段的景點ID，格式如：
                {
                    '上午': ['id1', 'id2'],
                    '中餐': ['id3', 'id4']
                }
            unique_requirement: List[Dict]
                使用者的特殊需求，例如：
                [{'無障礙': True, '適合兒童': True}]

        Returns:
            List[Dict]: 景點的詳細資料列表
        """
        unique_requirement = [{'無障礙': False}]

        return pandas_search(
            system='trip',
            system_input=placeIDs,
            special_request_list=unique_requirement,
        )

    def _add_duration(self, places: List[Dict]) -> List[Dict]:
        """為地點加入停留時間資訊

        Args:
            places: List[Dict] - 地點列表

        Returns:
            List[Dict] - 加入duration後的地點列表
        """
        try:
            # 讀取duration資料
            duration_df = pd.read_csv('data/emotion_analysis.csv')

            # 建立查找字典
            duration_dict = duration_df.set_index(
                'placeID')['停留時間'].to_dict()

            # 為每個地點加入duration
            for place in places:
                place_id = place.get('place_id')
                if place_id in duration_dict:
                    place['duration_min'] = int(duration_dict[place_id])
                    place['label'] = place['label_type']
                else:
                    # 找不到資料時給預設值
                    place['duration_min'] = 60

            return places

        except Exception as e:
            print(f"加入duration資訊時發生錯誤: {str(e)}")
            # 發生錯誤時返回原始資料
            return places

    def _plan_trip(
        self,
        location_details: List[Dict],
        base_requirement: List[Dict],
        previous_trip: List[Dict] = None,
        restart_index: int = None
    ) -> List[Dict]:
        """根據景點資料和基本需求規劃行程

        Args:
            location_details: List[Dict] - 景點詳細資料列表
            base_requirement: List[Dict] - 基本需求，如時間、交通方式等
            previous_trip: List[Dict] - 之前規劃的行程(選填)
            restart_index: int - 從哪個行程點重新開始(選填)

        Returns:
            List[Dict]: 格式化的行程規劃結果
        """
        # 使用已初始化的 trip_planner
        return self.trip_planner.plan_trip(
            locations=location_details,
            requirement=base_requirement,
            previous_trip=previous_trip,
            restart_index=restart_index
        )

    def _prepare_input_text(
        self,
        text: str = "",
        line_id: str = "test_user_id",
        previous_trip: List[Dict] = None
    ) -> str:
        """準備給LLM的輸入文字

        Returns:
            str: 組合後的輸入文字
        """
        # 取得歷史狀態
        history = trip_db.get_history_status(line_id)
        # if not history:
        #     return text

        # 需要整理就先整理和儲存
        if history["needs_summary"]:
            messages = [m["text"] for m in history["new_messages"]]
            # 如果有舊摘要就加入
            if history["summary"]:
                messages.insert(0, history["summary"])

            try:
                # 過濾None並轉字串
                valid_messages = [
                    str(msg) for msg in messages if msg is not None
                ]
                if valid_messages:
                    # 整理歷史
                    summary = self.LLM_obj.summarize_history(
                        "\n".join(valid_messages)
                    )
                else:
                    summary = "目前沒有可總結的歷史對話"
            except Exception as e:
                print(f"處理歷史訊息時發生錯誤: {str(e)}")
                summary = "總結歷史訊息時發生錯誤"

            trip_db.update_summary(line_id, summary)
            # 用新摘要
            history["summary"] = summary
            history["new_messages"] = []

        # 組合輸入
        parts = []

        if history["summary"]:
            parts.append(f"用戶歷史偏好:\n{history['summary']}")

        if history["new_messages"]:
            parts.append("新對話:\n" + "\n".join(m["text"]
                         for m in history["new_messages"]))

        if previous_trip:
            parts.append("之前的行程:\n" + str(previous_trip))

        parts.append(f"當前輸入:\n{text}")

        return "\n\n".join(parts)


def format_history_for_llm(history: List[Dict]) -> str:
    """把歷史記錄格式化成適合LLM的文字格式

    Args:
        history: 從MongoDB取得的歷史記錄

    Returns:
        str: 格式化後的歷史文字
    """
    if not history:
        return "目前沒有歷史對話記錄。"

    # 按時間排序(雖然資料庫已排序,但再確保一次)
    sorted_history = sorted(history, key=lambda x: x["timestamp"])

    # 組合文字
    formatted = "以下是用戶先前的對話記錄:\n\n"

    for record in sorted_history:
        # 格式化時間 (轉換成當地時間)
        time_str = record["timestamp"].astimezone().strftime(
            "%Y-%m-%d %H:%M")
        formatted += f"{time_str}: {record['text']}\n"

    return formatted


def init_config():
    """初始化設定

    載入環境變數並整理成設定字典

    Returns:
        dict: 包含所有 API 設定的字典，包括:
            - jina_url: Jina API 端點
            - jina_headers_Authorization: Jina 認證金鑰
            - qdrant_url: Qdrant 伺服器位址
            - qdrant_api_key: Qdrant 存取金鑰
            - ChatGPT_api_key: OpenAI API 金鑰
    """
    # 直接載入環境變數，這樣在容器中也能正常運作
    load_dotenv()

    config = {
        'jina_url': os.getenv('jina_url'),
        'jina_headers_Authorization': os.getenv('jina_headers_Authorization'),
        'qdrant_url': os.getenv('qdrant_url'),
        'qdrant_api_key': os.getenv('qdrant_api_key'),
        'ChatGPT_api_key': os.getenv('ChatGPT_api_key')
    }

    # 驗證所有設定都存在
    missing = [key for key, value in config.items() if not value]
    if missing:
        raise ValueError(f"缺少必要的API設定: {', '.join(missing)}")

    return config


if __name__ == "__main__":
    try:
        config = init_config()
        controller_instance = TripController(config)

        # test_input = "開車，想去台北文青的地方，吃午餐要便宜又好吃，下午想去逛有特色的景點，晚餐要可以跟朋友聚餐"
        test_input = "不喜歡第五個點"
        result = controller_instance.process_message(test_input)
        controller_instance.trip_planner.print_itinerary(result)

    except Exception as e:
        print("DEBUG: ", str(e))  # 完整錯誤訊息
