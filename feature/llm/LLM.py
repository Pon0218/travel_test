import openai
import json
from dotenv import load_dotenv
import os
import concurrent.futures  # 引入並行處理模組

from feature.llm.utils import system_prompt
from feature.llm.utils.extractor.plan_basic_req_extractor import plan_basic_req_extractor
from feature.llm.utils.extractor.special_request_extractor import special_request_extractor
from feature.llm.utils.extractor.trip_basic_req_extractor import trip_basic_req_extractor
from feature.llm.utils.extractor.plan_preferred_statement_extractor import plan_preferred_statement_extractor
from feature.llm.utils.extractor.trip_preferred_statement_extractor import trip_preferred_statement_extractor
from feature.llm.utils.extractor.trip_restart_extractor import trip_restart_extractor
from feature.llm.utils.extractor.summarize_history_extractor import summarize_history_extractor

class LLM_Manager:
    def __init__(self, ChatGPT_api_key):
        openai.api_key = ChatGPT_api_key  # 使用 ChatGPT_api_key 來設定 OpenAI API 金鑰

    def __Query(self, prompt, user_input, format):
        """
        使用 OpenAI API 生成回應
        format = "list" or "List[Dict]"
        """
        # 檢查類型檢查和轉換,使用 json.dumps 轉換為字符串
        if isinstance(user_input, (list, dict)):
            user_input = json.dumps(user_input, ensure_ascii=False)

        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": user_input}
            ],
            temperature=0.7,
            max_tokens=800
        )
        content = response['choices'][0]['message']['content'].strip()
        content = (
            content
                .replace("：", ":")
                .replace("，", ",")
                .replace("。", ",")
                .replace("、", " ")
                .replace("？", "?")
                .replace("\n", " ")
        )

        try:
            data = json.loads(content)

            if format == "List[Dict]":
                return [data]
            return data

        except json.JSONDecodeError:
            try:
                # 找第一個 '{' 或 '[' 的位置
                start = min(content.find('{'), content.find('['))
                # 找最後一個 '}' 或 ']' 的位置
                end = max(content.rfind('}'), content.rfind(']')) + 1

                # 擷取並解析JSON部分
                json_str = content[start:end]
                data = json.loads(json_str)

                if format == "List[Dict]":
                    return [data]
                return data

            except Exception as e:
                print('LLM 在解 json 格式時即錯誤，將其回傳 "none" 給提取器輸出 預設值')
                return 'none'

    def summarize_history(self, history_text: str) -> str:
        """整理歷史記錄成摘要文字

        Args:
            history_text: 對話記錄文字

        Returns:
            str: 整理後的摘要
        """
        response = self.__Query(
            prompt=system_prompt.summarize_history,
            user_input=history_text,
            format="List"
        )

        '''
        歷史大綱 LLM 認證程序 
        '''
        print('========歷史大綱 LLM 認證程序========')
        print('認證 - 總共一項資料 :')
        # 歷史大剛提取器，確保  history 值格式正確無誤，為 list, length=1, 內容為一個字串, 字數大於 limit
        response = summarize_history_extractor(response, 10)
        print('=======================================\n\n')

        # __Query會回傳['歷史總結語句'],取第一個元素
        return response[0]


    def Thinking_fun(self, user_input):
        # 使用 ThreadPoolExecutor 來並行處理 API 請求
        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = {
                'Thinking_A': executor.submit(self.__Query, system_prompt.Thinking_A, user_input, "List[5 x Dict]"),
                'Thinking_B': executor.submit(self.__Query, system_prompt.Thinking_B, user_input, "List[Dict]"),
                'Thinking_C': executor.submit(self.__Query, system_prompt.Thinking_C, user_input, "List[Dict]"),
                'restart': executor.submit(self.__Query, system_prompt.restart, user_input, "List")
            }

            # 等待所有任務完成並取得結果
            Thinking = []
            for future in futures.values():
                result = future.result()
                Thinking.append(result)
            
            '''
            旅遊推薦端 LLM 認證程序 
            '''
            print('========旅遊推薦端 LLM 認證程序========')
            print('認證 - 總共四項資料 :')
            # 使用偏好語句篩選器，確保每句字數 > limit
            Thinking[0] = trip_preferred_statement_extractor(Thinking[0], limit=10)

            # 使用特殊篩選提取器，確保其格式無誤
            Thinking[1] = special_request_extractor(Thinking[1]) 

            # 使用旅遊基本需求提取器，除了 [出發地點、結束地點] 只能確認是字串格式外 , 確保LLM格式無誤
            Thinking[2] = trip_basic_req_extractor(Thinking[2])

            # 使用 restart 提取器 確保  LLM restart 值格式正確無誤，為 [int], length=1
            Thinking[3] = trip_restart_extractor(Thinking[3])
            print('=======================================\n\n')

            return Thinking

    def Cloud_fun(self, user_input):
        # 使用 ThreadPoolExecutor 來並行處理 API 請求
        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = {
                'Cloud_A': executor.submit(self.__Query, system_prompt.Cloud_A, user_input, "List"),
                'Cloud_B': executor.submit(self.__Query, system_prompt.Cloud_B, user_input, "List[Dict]"),
                'Cloud_C': executor.submit(self.__Query, system_prompt.Cloud_C, user_input, "List[Dict]")
            }

            # 等待所有任務完成並取得結果
            Cloud = []
            for future in futures.values():
                result = future.result()
                Cloud.append(result)

            '''
            情境搜索端 LLM 認證程序 
            '''
            print('========情境搜索端 LLM 認證程序========')
            print('認證 - 總共三項資料 :')
            # 使用情境搜尋偏好句篩選器，確保格式字串長度無誤
            Cloud[0] = plan_preferred_statement_extractor(Cloud[0], limit = 10)

            # 使用特殊篩選提取器，確保其格式無誤
            Cloud[1] = special_request_extractor(Cloud[1]) 

            # 使用旅遊基本需求提取器, 確保LLM格式無誤
            Cloud[2] = plan_basic_req_extractor(Cloud[2])
            print('=======================================\n\n')

            return Cloud


if __name__ == "__main__":
    from pprint import pprint
    # 從環境變量中讀取 OpenAI API 金鑰
    load_dotenv()
    ChatGPT_api_key = os.getenv('ChatGPT_api_key')

    # 初始化物件
    LLM_obj = LLM_Manager(ChatGPT_api_key)

    # 呼叫 Thinking 和 Cloud 的並行處理函數
    user_input = "想去台北文青的地方，吃午餐要便宜又好吃，下午想去逛有特色的景點，晚餐要可以跟朋友聚餐"
    
    
    # ==============旅遊推薦 LLM 測試======================================
    results = LLM_obj.Thinking_fun(user_input)
    print('======旅遊推薦======')
    print(f'input query = {user_input}\n')
    pprint(results, sort_dicts=False)
    print('\n\n')

    # ==============旅遊推薦 歷史綱要 測試=================================
    results = LLM_obj.summarize_history(user_input)
    print('======歷史綱要 測試======')
    print(f'input query = {user_input}\n')
    pprint(results, sort_dicts=False)
    print('\n\n')

    # ===============情境搜所 LLM 測試=====================================
    results = LLM_obj.Cloud_fun(user_input)
    print('======情境搜索======')
    print(f'input query = {user_input}\n')
    pprint(results, sort_dicts=False)
