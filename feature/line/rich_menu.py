"""
LINE Rich Menu模組 - 混合使用MessageAction和PostbackAction

負責:
1. 建立客製化rich menu
2. 混合不同類型的action處理
3. 處理圖片生成
"""

import io
import time
from linebot.v3.messaging import (
    Configuration,
    RichMenuRequest,
    RichMenuArea,
    RichMenuBounds,
    RichMenuSize,
    PostbackAction,
    MessageAction,
    ApiClient,
    MessagingApi,
    RichMenuSwitchAction,
    CreateRichMenuAliasRequest,
)
from PIL import Image, ImageDraw, ImageFont
import requests

# 目前在Docker上跑會有錯誤訊息，但功能正常: 待解決


class RichMenuManager:
    """Rich Menu管理類別"""

    def __init__(self, channel_access_token: str):
        """
        初始化

        Args:
            channel_access_token: LINE Bot的channel access token
        """
        self.channel_access_token = channel_access_token
        self.configuration = Configuration(access_token=channel_access_token)

    def create_rich_menu(self):
        """建立聊天室的Rich Menu選單

        流程:
        1. 清理現有的rich menu和alias
        2. 建立新的search menu和trip menu
        3. 設定alias對應關係
        4. 設定預設選單為trip menu

        錯誤處理:
        - 404錯誤(找不到資源)會被優雅處理
        - 重複執行會被防止
        - 關鍵錯誤會拋出異常

        Returns:
            tuple: (trip_menu_id, search_menu_id) 建立的兩個選單ID
        """
        api_client = ApiClient(self.configuration)
        messaging_api = MessagingApi(api_client)

        # 用來控制延遲的helper function
        def wait(seconds: int = 1):
            time.sleep(seconds)

        try:
            print("開始建立Rich Menu...")

            # 1. 清理現有資源
            print("清理現有資源...")
            try:
                # 先刪除alias
                for alias in ["trip_menu", "search_menu"]:
                    try:
                        messaging_api.delete_rich_menu_alias(alias)
                        print(f"- 成功刪除alias: {alias}")
                    except Exception as e:
                        if '404' not in str(e):  # 忽略404錯誤
                            print(f"- 刪除alias {alias} 時發生錯誤: {str(e)}")

                wait()  # 等待alias刪除完成

                # 再刪除所有menu
                rich_menu_list = messaging_api.get_rich_menu_list()
                if hasattr(rich_menu_list, 'richmenus'):
                    for menu in rich_menu_list.richmenus:
                        try:
                            messaging_api.delete_rich_menu(
                                rich_menu_id=menu.rich_menu_id)
                            print(f"- 成功刪除menu: {menu.rich_menu_id}")
                        except Exception as e:
                            if '404' not in str(e):  # 忽略404錯誤
                                print(f"- 刪除menu時發生錯誤: {str(e)}")

            except Exception as e:
                print(f"清理資源時發生錯誤: {str(e)}")

            wait(2)  # 確保清理完成

            # 2. 建立新的menu
            print("\n建立新的Rich Menu...")
            try:
                search_menu_id = self._create_search_menu()
                print(f"- 建立search menu成功: {search_menu_id}")

                wait()  # 等待第一個menu建立完成

                trip_menu_id = self._create_trip_menu()
                print(f"- 建立trip menu成功: {trip_menu_id}")

                wait()  # 等待第二個menu建立完成

            except Exception as e:
                print(f"建立menu時發生錯誤: {str(e)}")
                raise e

            # 3. 設定alias
            print("\n設定Rich Menu alias...")
            try:
                messaging_api.create_rich_menu_alias(
                    CreateRichMenuAliasRequest(
                        richMenuAliasId="search_menu",
                        richMenuId=search_menu_id
                    )
                )
                print("- 設定search_menu alias成功")

                wait()  # 等待第一個alias設定完成

                messaging_api.create_rich_menu_alias(
                    CreateRichMenuAliasRequest(
                        richMenuAliasId="trip_menu",
                        richMenuId=trip_menu_id
                    )
                )
                print("- 設定trip_menu alias成功")

            except Exception as e:
                if 'conflict' in str(e):
                    print("- Alias已存在,略過設定")
                else:
                    print(f"設定alias時發生錯誤: {str(e)}")
                    raise e

            # 4. 設定預設選單
            try:
                messaging_api.set_default_rich_menu(rich_menu_id=trip_menu_id)
                print("\n成功設定預設選單為trip menu")
            except Exception as e:
                print(f"設定預設選單時發生錯誤: {str(e)}")
                raise e

            print("\nRich Menu建立完成!")
            return trip_menu_id, search_menu_id

        except Exception as e:
            print(f"\n建立Rich Menu時發生嚴重錯誤: {str(e)}")
            # 清理資源
            try:
                for alias in ["trip_menu", "search_menu"]:
                    try:
                        messaging_api.delete_rich_menu_alias(alias)
                    except:
                        pass
            except:
                pass
            raise e

    def _create_trip_menu(self):
        """建立旅遊規劃頁面選單"""

        rich_menu = RichMenuRequest(
            size=RichMenuSize(width=2500, height=1000),
            selected=True,
            name="Trip Menu",
            chat_bar_text="功能選單",
            areas=[
                # 上方Tab - 切換區域
                RichMenuArea(
                    bounds=RichMenuBounds(x=0, y=0, width=1250, height=200),
                    action=RichMenuSwitchAction(
                        rich_menu_alias_id="search_menu", data="switch")

                ),
                RichMenuArea(
                    bounds=RichMenuBounds(x=1250, y=0, width=1250, height=200),
                    action=RichMenuSwitchAction(
                        rich_menu_alias_id="trip_menu", data="switch")
                ),

                # 功能區域
                RichMenuArea(  # 規劃行程
                    bounds=RichMenuBounds(x=0, y=200, width=833, height=800),
                    action=PostbackAction(data="action=trip_planning")
                ),
                RichMenuArea(  # 重新規劃
                    bounds=RichMenuBounds(
                        x=833, y=200, width=834, height=800),
                    action=MessageAction(text="紀錄初始化")
                ),
                RichMenuArea(  # 功能說明
                    bounds=RichMenuBounds(
                        x=1667, y=200, width=833, height=800),
                    action=MessageAction(text="旅遊規劃說明")
                )
            ]
        )

        # 建立選單
        api_client = ApiClient(self.configuration)
        messageing_api = MessagingApi(api_client)
        rich_menu_id = messageing_api.create_rich_menu(
            rich_menu_request=rich_menu
        )

        # 上傳選單圖片
        img = self._create_trip_menu_image()
        self._upload_menu_image(rich_menu_id.rich_menu_id, img)

        return rich_menu_id.rich_menu_id

    def _create_search_menu(self):
        """建立情境搜索頁面選單"""

        rich_menu = RichMenuRequest(
            size=RichMenuSize(width=2500, height=1000),
            selected=False,
            name="Search Menu",
            chat_bar_text="功能選單",
            areas=[
                # Tabs
                RichMenuArea(
                    bounds=RichMenuBounds(
                        x=0, y=0, width=1250, height=200),
                    action=RichMenuSwitchAction(
                        rich_menu_alias_id="search_menu", data="switch")
                ),
                RichMenuArea(
                    bounds=RichMenuBounds(
                        x=1250, y=0, width=1250, height=200),
                    action=RichMenuSwitchAction(
                        rich_menu_alias_id="trip_menu", data="switch")
                ),

                # 功能按鈕
                RichMenuArea(
                    bounds=RichMenuBounds(
                        x=0, y=200, width=833, height=800),
                    action=MessageAction(text="我想進行情境搜索", label="情境搜索")
                ),
                RichMenuArea(
                    bounds=RichMenuBounds(
                        x=833, y=200, width=834, height=800),
                    action=MessageAction(text="顯示我的收藏", label="我的收藏")
                ),
                RichMenuArea(
                    bounds=RichMenuBounds(
                        x=1667, y=200, width=833, height=800),
                    action=MessageAction(text="情境搜索說明", label="說明")
                )
            ]
        )

        # 建立選單
        api_client = ApiClient(self.configuration)
        messageing_api = MessagingApi(api_client)
        rich_menu_id = messageing_api.create_rich_menu(
            rich_menu_request=rich_menu)

        # 上傳選單圖片
        img = self._create_search_menu_image()
        self._upload_menu_image(rich_menu_id.rich_menu_id, img)

        return rich_menu_id.rich_menu_id

    def _create_trip_menu_image(self) -> bytes:
        """建立旅遊規劃頁面圖片"""
        # 建立畫布
        img = Image.new('RGB', (2500, 1000), '#d1cdcd')
        draw = ImageDraw.Draw(img)

        # 字型設定
        tab_font = ImageFont.truetype('data/fonts/msjh.ttc', 100)  # 改用微軟正黑體
        current_tab_font = ImageFont.truetype('data/fonts/msjhbd.ttc', 105)
        button_font = ImageFont.truetype('data/fonts/msjh.ttc', 120)

        # 繪製Tab區域
        draw.rectangle([0, 0, 1250, 200], fill='#bbbbbb')  # 淺灰色底
        draw.rectangle([1250, 0, 2500, 200], fill='#d1cdcd')  # 當前頁面

        draw.text((625, 100), "情境搜索", font=tab_font,
                  anchor='mm', fill='#666666')
        draw.text((1875, 100), "旅遊規劃", font=current_tab_font,
                  anchor='mm', fill='#000000')

        # 功能按鈕區域
        button_height = 500  # 按鈕高度
        y_start = 250  # 按鈕起始y座標

        # 行程規劃按鈕 (左)
        self._draw_rounded_rectangle(
            draw,
            (250, y_start, 250 + button_height, y_start + button_height),
            '#f5f5f5',
            radius=50
        )

        # 加入icon
        travel_icon = Image.open(
            'icons/travel.png').resize((button_height, button_height))
        if 'A' in travel_icon.getbands():
            img.paste(travel_icon, (250, y_start), travel_icon)

        # 文字
        draw.text((500, y_start + button_height + 100), "規劃行程",
                  font=button_font, anchor='mm', fill='black')

        # 重新規劃按鈕 (中)
        self._draw_rounded_rectangle(
            draw,
            (1000, y_start, 1000 + button_height, y_start + button_height),
            '#f5f5f5',
            radius=50
        )

        # 加入icon
        reset_icon = Image.open(
            'icons/reset.png').resize((button_height, button_height))
        if 'A' in reset_icon.getbands():
            img.paste(reset_icon, (1000, y_start), reset_icon)

        draw.text((1250, y_start + button_height + 100), "紀錄初始化",
                  font=button_font, anchor='mm', fill='black')

        # 使用說明按鈕 (右)
        self._draw_rounded_rectangle(
            draw,
            (1750, y_start, 1750 + button_height, y_start + button_height),
            '#f5f5f5',
            radius=50
        )

        # 加入icon
        help_icon = Image.open(
            'icons/help.png').resize((button_height, button_height))
        if 'A' in help_icon.getbands():
            img.paste(help_icon, (1750, y_start), help_icon)

        draw.text((2000, y_start + button_height + 100), "使用說明",
                  font=button_font, anchor='mm', fill='black')

        # 轉換為bytes
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='PNG')
        return img_byte_arr.getvalue()

    def _create_search_menu_image(self) -> bytes:
        """建立情境搜索頁面圖片"""
        # 建立畫布
        img = Image.new('RGB', (2500, 1000), '#d1cdcd')
        draw = ImageDraw.Draw(img)

        # 字型設定
        tab_font = ImageFont.truetype('data/fonts/msjh.ttc', 100)  # 改用微軟正黑體
        current_tab_font = ImageFont.truetype('data/fonts/msjhbd.ttc', 105)
        button_font = ImageFont.truetype('data/fonts/msjh.ttc', 120)

        # 繪製Tab區域
        draw.rectangle([0, 0, 1250, 200], fill='#d1cdcd')  # 當前頁面
        draw.rectangle([1250, 0, 2500, 200], fill='#bbbbbb')

        draw.text((625, 100), "情境搜索", font=current_tab_font,
                  anchor='mm', fill='#000000')
        draw.text((1875, 100), "旅遊規劃", font=tab_font,
                  anchor='mm', fill='#666666')

        # 功能按鈕區域
        button_height = 500  # 按鈕高度
        y_start = 250  # 按鈕起始y座標

        # 開始搜索按鈕 (左)
        self._draw_rounded_rectangle(
            draw,
            (250, y_start, 250 + button_height, y_start + button_height),
            '#f5f5f5',
            radius=50
        )

        # 加入icon
        search_icon = Image.open(
            'icons/search.png').resize((button_height, button_height))
        if 'A' in search_icon.getbands():
            img.paste(search_icon, (250, y_start), search_icon)

        # 文字
        draw.text((500, y_start + button_height + 100), "開始搜索",
                  font=button_font, anchor='mm', fill='black')

        # 我的收藏按鈕 (中)
        self._draw_rounded_rectangle(
            draw,
            (1000, y_start, 1000 + button_height, y_start + button_height),
            '#f5f5f5',
            radius=50
        )

        # 加入icon
        favorite_icon = Image.open(
            'icons/favorite.png').resize((button_height, button_height))
        if 'A' in favorite_icon.getbands():
            img.paste(favorite_icon, (1000, y_start), favorite_icon)

        draw.text((1250, y_start + button_height + 100), "我的收藏",
                  font=button_font, anchor='mm', fill='black')

        # 使用說明按鈕 (右)
        self._draw_rounded_rectangle(
            draw,
            (1750, y_start, 1750 + button_height, y_start + button_height),
            '#f5f5f5',
            radius=50
        )

        # 加入icon
        help_icon = Image.open(
            'icons/help.png').resize((button_height, button_height))
        if 'A' in help_icon.getbands():
            img.paste(help_icon, (1750, y_start), help_icon)

        draw.text((2000, y_start + button_height + 100), "使用說明",
                  font=button_font, anchor='mm', fill='black')

        # 轉換為bytes
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='PNG')
        return img_byte_arr.getvalue()

    def _draw_rounded_rectangle(
        self,
        draw: ImageDraw,
        coords: tuple,
        color: str,
        radius: int = 20
    ):
        """繪製圓角矩形

        Args:
            draw: ImageDraw物件
            coords: 矩形座標 (x1, y1, x2, y2)
            color: 填充顏色
            radius: 圓角半徑
        """
        x1, y1, x2, y2 = coords
        diameter = radius * 2

        # 繪製主要矩形
        draw.rectangle([x1+radius, y1, x2-radius, y2], fill=color)
        draw.rectangle([x1, y1+radius, x2, y2-radius], fill=color)

        # 繪製四個圓角
        draw.ellipse([x1, y1, x1+diameter, y1+diameter], fill=color)  # 左上
        draw.ellipse([x2-diameter, y1, x2, y1+diameter], fill=color)  # 右上
        draw.ellipse([x1, y2-diameter, x1+diameter, y2], fill=color)  # 左下
        draw.ellipse([x2-diameter, y2-diameter, x2, y2], fill=color)  # 右下

    def _get_placeholder_image(self, width: int, height: int) -> Image:
        """生成簡單的純色圖片作為icon

        Args:
            width: 寬度
            height: 高度

        Returns:
            PIL.Image: 生成的圖片物件
        """
        # 生成淺藍色的矩形圖片
        img = Image.new('RGB', (width, height), '#87CEEB')  # 淺藍色
        draw = ImageDraw.Draw(img)

        # 繪製邊框
        draw.rectangle([0, 0, width-1, height-1],
                       outline='#4682B4', width=2)  # 深藍色邊框

        return img

    def _upload_menu_image(self, rich_menu_id: str, image_data: bytes):
        """上傳選單圖片"""
        url = f'https://api-data.line.me/v2/bot/richmenu/{
            rich_menu_id}/content'
        headers = {
            'Authorization': f'Bearer {self.channel_access_token}',
            'Content-Type': 'image/png'
        }

        response = requests.post(url, headers=headers, data=image_data)
        response.raise_for_status()
