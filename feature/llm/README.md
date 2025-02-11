## 環境配置
- 需要套件 : pip install openai python-dotenv
- 配置 .env 檔 : ChatGPT_api_key=your_openai_api_key  #放入自己的chatGPT api key
- 使用說明: 需先初始化套件 ex: LLM_obj = LLM_Manager(ChatGPT_api_key)
##  LLM_Manager

- `def Thinking_fun()` : 旅遊推薦包含了3種執行方式 
    - `Thinking_A` : 旅遊各時段的形容一句話 . type:List [ Dict ]
        傳送到 a > 向量搜尋
    - `Thinking_B` : 確認特殊要求 . type:List [ Dict ]
        傳送到 b > 結構搜尋
    - `Thinking_C` : 用戶基本要求,若無則"none". type:List [ Dict ]
        傳送到 c > Trip

- `def Cloud_fun()` : 情境搜索包含了3種執行方式 
    - `Cloud_A` : 客戶形容的一句話 . type:List
        傳送到 a > 向量搜尋
    - `Cloud_B` : 確認特殊要求 . type:List [ Dict ]
        傳送到 b > 結構搜尋
    - `Cloud_C` : 用戶基本要求,若無則"none". type:List [ Dict ]
        傳送到 c > Plan

- `def store_fun()` :  推薦店家
    - 接收 Cloud_fun().Cloud_A 出來的 a
    - 接收 Plan 篩選出的15筆資料
    - 最後篩選出3筆最符合的資料
