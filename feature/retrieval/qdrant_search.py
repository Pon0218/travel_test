from qdrant_client import QdrantClient, models
from dotenv import dotenv_values

from .utils.jina_embedding import jina_embedding
from .utils.qdrant_control import qdrant_manager

class qdrant_search:
    '''
    #### 向量搜尋端 :
    ---
    - input :  

        ```
        collection_name = 想要搜尋的桶子名稱
        score_threshold = 分數限制 
        limit = 回傳數量限制
        config = {
                    'jina_url':str, 
                    'jina_headers_Authorization':str,
                    'qdrant_url': str,
                    'qdrant_api_key': str
                }
        black_list 設定要過濾的 placeID 清單
        ```
    
    - 

    ---
    - 流程 :
        1. vector = 將 ["形容客戶行程的一句話"] 直接向量化
        2. 使用 vector 搜尋 qdrant 回傳 '相似度 > 某個分數' 的資料

    ---
    - method :

        ```
        .cloud_search( input_query: list[str] = ["形容客戶行程的一句話"] )
        .trip_search( input_query: dict[list] = { "上午" : "形容客戶行程的一句話"})
        ```
    '''
    def __init__(
                self,
                collection_name: str= 'view_restaurant',
                score_threshold: float=0,
                limit: int=1000,
                config: dict = {
                                'jina_url':str, 
                                'jina_headers_Authorization':str,
                                'qdrant_url': str,
                                'qdrant_api_key': str
                                },
                black_list: list=[],
                ):
        
        self.colleciton_name = collection_name
        self.config = config
        self.score_threshold = score_threshold
        self.limit = limit
        self.black_list = black_list
        


    def __search_query(self, input_query):
        '''
        - 主函數，負責搜尋
        - output :  

            ```
            return [{
                        "Place ID 1":{"分數":"int"} ,      # 相似分數 
                        "Place ID 2":{"分數":"int"} , 
                        …, 
                        "Place ID n":{"分數":"int"} 
                    }]
            ```
        '''
        config = self.config

         # 1. 將 ["形容客戶行程的一句話"] 直接向量化
        embedding_data = jina_embedding(input_query, '', config['jina_url'], config['jina_headers_Authorization'])
        vector = embedding_data['embedding']   # dim = 1024

        # 2. 使用 vector 搜尋 qdrant 回傳 '相似度 > 某個分數' 的資料
        qdrant_obj = qdrant_manager(collection_name=self.colleciton_name, 
                                    qdrant_url=config.get("qdrant_url"),
                                    qdrant_api_key= config.get("qdrant_api_key"))
        result = qdrant_obj.search_vector(vector, self.score_threshold, self.limit, self.black_list)
        return result


    def cloud_search(self, input_query: list[str])-> list[dict]:
        '''
        - 對情境搜尋
        - input :

            ```
            input_query: list[str] = ["形容客戶行程的一句話"]
            ```
        - output :

            ```
            return [{
                "Place ID 1":{"分數":"int"} ,      # 相似分數 
                "Place ID 2":{"分數":"int"} , 
                …, 
                "Place ID n":{"分數":"int"} 
            }]
            ```
        '''
        result = self.__search_query(input_query)
        return result
    
    def trip_search(self, input_query: dict)-> dict[list]: 
        '''
        - 對旅遊演算法
        - input :

            ```
            input_query: dict = { "上午" : "形容客戶行程的一句話"}
            ```
        output :

            ```
            return { period : ["PlaceID", "PlaceID", …, "PlaceID"]} 
            ```
        '''
        period, text = next(iter(input_query.items()))
        result = list(self.__search_query(text)[0].keys())

        return {period : result}


if __name__ == "__main__":
    # 加載環境變量
    config = dotenv_values("./.env")
    if len(config) == 0:
        print('please check .env path')

    qdrant_obj = qdrant_search(collection_name= 'view_restaurant_test', 
                               config= config,
                               score_threshold= 0,
                               limit=50)

    # 旅遊搜索
    input_query = {'上午': '喜歡在文青咖啡廳裡享受幽靜且美麗的裝潢'}
    result = qdrant_obj.trip_search(input_query)

    # print(result)
    # print(len(result[0]))

    # ===============================================================
    # 情境搜索

    qdrant_obj = qdrant_search(
        collection_name= 'weii-black-list-test', 
        config= config,
        score_threshold= -1,
        limit=1000,
        # black_list=[],
        black_list= ['ChIJ_5EDThKpQjQRf4L6uxaRpiI', 'ChIJ_3YUOnOsQjQRxaKUQca9pbg', 'ChIJ_3Drk2CpQjQRj60tccm_S-c',
                    'ChIJ_0k1Uu2rQjQRHE3673mDzZw', 'ChIJ_4RNViOsQjQRIMcdxY-zq7E', 'ChIJ_2_GKFqlQjQRGAF9qRkQYRM', 
                    'ChIJ_2re1N2oQjQRSUIvOgjlJfc', 'ChIJ_5VtCtioQjQRkjceKXaxmP4', 'ChIJ_3LZiLyvQjQR3SvEA0zV4Hk',
                    # 'ChIJ-_1rl4WpQjQRFIxRQ1xCpw0'
                    ]
    )

    # 情境搜索
    input_query = ['喜歡在文青咖啡廳裡享受幽靜且美麗的裝潢']
    result = qdrant_obj.cloud_search(input_query)
    
    print(result)