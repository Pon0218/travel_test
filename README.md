# travel_ROUTER / Tibame Project
---

## 人員控制
### <旅遊演算法> 各部位工作人員
1. 澎澎 : Line 端
2. ABBY : LLM 端
3. 石頭 : 向量搜尋端
4. 瑜庭 : 關聯式搜尋端
5. 啓舜 : 旅遊演算法、main_trip.py

### <情境搜尋演算法> 各部位工作人員
1. 澎澎 : Line 端
2. ABBY : LLM 端
3. 石頭 : 向量搜尋端
4. 瑜庭 : 關聯式搜尋端、情境搜尋演算法
5. 家偉 : main_plan.py

---
## 分支控制
### 常駐分支
1. 程珣
   * master ( main ): 提供 release 合併 / 已上線分支
   * develop : 提供穩定版本 integration 合併
   * integration : 提供所有 feature 基於此分支開發

### 任務分支 / 測試bug 修正
1. 程珣
    * release : 提供 develop 合併 / 上線前測試
    * hotfix : release 、master 分支 bug 修復

### 任務分支 / 功能開發 
#### --> 基於 integration 分支
1. 澎澎
    * `feature/line` : Line 端各功能開發
2. ABBY
    * `feature/LLM` : LLM 端各功能開發
3. 石頭
    * `feature/retrival` : 向量搜尋功能開發
4. 瑜庭
    * `feature/SQL` : 關聯式搜尋功能開發
    * `feature/plan` : 情境搜尋演算法開發
5. 家偉
    * `feature/main_plan` : 情境搜尋演算法 main 建置
6. 啓舜
    * `feature/trip` : 旅遊演算法功能開發
    * `feature/main_trip` : 旅遊演算法 main 建置

---
## 資料夾樹狀圖
```
project-root/
├── feature/
│   ├── line/               # 澎澎負責的 Line 端各功能開發
│   ├── llm/                # ABBY 負責的 LLM 端各功能開發
│   ├── retrieval/          # 石頭負責的向量搜尋功能開發
│   ├── sql/                # 瑜庭負責的關聯式搜尋功能開發
│   ├── plan/               # 瑜庭負責的情境搜尋演算法開發
│   └── trip/               # 啓舜負責的旅遊演算法功能開發
├── main/
│   ├── main_plan/          # 家偉負責的情境搜尋演算法 main 建置
│   └── main_trip/          # 啓舜負責的旅遊演算法 main 建置
└── README.md               # 專案簡介與基本說明
```

---
## 各接口、負責人詳細資訊
* https://docs.google.com/presentation/d/18xqwSCuFtxsEjBkQ4jkxNkvXWN2dcOt_0aOsSer9k_g/edit#slide=id.g32640ae6244_1_32

---
## 注意事項
* 每個方框都是一個 function
* 請把每一個功能寫成一個 function !!!
* 內部內容、順序、type一定不可更動，必須符合規範 !!!
* 各部位務必再確認接收參數的部位是否符合要求
* 盡量使利用模組化的方式建置程式碼
  
---
#### 分支示例
![image](https://github.com/user-attachments/assets/df3bc631-eb14-4bb9-bf7e-420841cc77f9)
