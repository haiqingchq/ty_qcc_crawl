import os
import time
from abc import ABC, abstractmethod

import pandas as pd
from playwright.sync_api import Page
from playwright.sync_api import Playwright
from tqdm import tqdm

from config import MIN_JS_PATH, HEADLESS, Disable_Blink_Features, User_Agent
from config import SCREENSHOT_HISTORY_PATH, CREDITS_HISTORY_PATH, base_path, SCREENSHOT_OUT_PATH, SCREENSHOT_DELAY
from crawl.common import ExcelHandler

"""
    https://bot.sannysoft.com/
    这个网站可以检测浏览器的属性是否正常
"""


class StartInterface(ABC):
    @abstractmethod
    def run(self, playwright: Playwright):
        """
            针对不同的需求，会有不一样的启动方式，粗粒度控制
        :return:
        """
        pass

    @abstractmethod
    def execute_by_custom(self, *args, **kwargs):
        """
            针对不同的需求，有不一样的执行逻辑，细粒度控制
        :param args:
        :param kwargs:
        :return:
        """
        pass


class Crawler(StartInterface):
    # 用来取消浏览器被控制异常属性的js代码
    stealth_js = open(MIN_JS_PATH, 'r').read()
    # 当前的登录状态
    login_flag = False
    # Excel 处理队形
    excel_handler: ExcelHandler = None
    # cookie 保存路径
    cookie_path: str = None

    def login(self, playwright: Playwright):
        raise NotImplementedError

    def check_login(self, playwright: Playwright):
        raise NotImplementedError

    def login_by_password(self, playwright: Playwright):
        raise NotImplementedError

    def init_page(self, playwright: Playwright):
        """
        初始化一个携带登录状态信息的page
        :param playwright:
        :return:
        """
        bs = playwright.chromium.launch(headless=HEADLESS, args=[f'--disable-blink-features={Disable_Blink_Features}',
                                                                 f'--user-agent={User_Agent}'])

        ctx = bs.new_context(storage_state=self.cookie_path)
        pg = ctx.new_page()
        pg.add_init_script(self.stealth_js)

        return pg, bs, ctx

    def run(self, playwright: Playwright):
        pass

    def execute_by_custom(self, *args, **kwargs):
        pass

    @staticmethod
    def read_history_list():
        """
        读取历史爬取的企业名称，避免重复爬取
        :return:
        """
        raise NotImplementedError

    def undo(self):
        raise NotImplementedError


class CreditCrawl(Crawler):
    def run(self, playwright: Playwright):
        page, browser, context = self.init_page(playwright=playwright)
        history_list = self.read_history_list()
        file = open(CREDITS_HISTORY_PATH, 'a', encoding='utf-8')

        business_list, credit_list = self.excel_handler.get_company_info_v1()
        target_dict = {}
        for business, credit in tqdm(zip(business_list, credit_list), desc="当前进度",
                                     unit="file", total=len(business_list)):
            if business not in history_list:
                try:
                    if pd.isna(credit):
                        credit = self.execute_by_custom(keyword=business, page=page)
                        target_dict[business] = credit
                    else:
                        continue
                    file.write(f'{business}\n')
                except AttributeError as e:
                    """
                        出现这个错误的情况有两种：
                            1、出现了访问的限制，导致没有进入到指定的页面
                            2、在qcc中不存在这家公司
                    """
                    continue
            else:
                continue
        self.excel_handler.save_company_info(target_dict=target_dict)
        file.close()
        context.close()
        browser.close()

    def execute_by_custom(self, *args, **kwargs):
        pass

    def get_credit_from_page(self, page: Page, url: str):
        raise NotImplementedError

    @staticmethod
    def read_history_list():
        """
        读取历史爬取的企业名称，避免重复爬取
        :return:
        """
        if os.path.exists(CREDITS_HISTORY_PATH):
            with open(CREDITS_HISTORY_PATH, 'r', encoding='utf-8') as file:
                lines = file.readlines()
            return [line.strip() for line in lines]
        return []


class ScreenshotCrawl(Crawler):
    def run(self, playwright: Playwright):
        page, browser, context = self.init_page(playwright=playwright)
        history_list = self.read_history_list()
        file = open(SCREENSHOT_HISTORY_PATH, 'a', encoding='utf-8')

        business_list, credit_list, filename_list = self.excel_handler.get_company_info_v2()

        for business, credit, filename in tqdm(zip(business_list, credit_list, filename_list), desc="当前进度",
                                               unit="file", total=len(business_list)):
            if business not in history_list:
                try:
                    if not pd.isna(business):
                        self.execute_by_custom(keyword=business, page=page, filename=filename)
                    else:
                        self.execute_by_custom(keyword=business, page=page, filename=filename)
                    file.write(f'{business}\n')
                except AttributeError as e:
                    """
                        出现这个错误的情况有两种：
                            1、出现了访问的限制，导致没有进入到指定的页面
                            2、在qcc中不存在这家公司
                    """
                    continue
            else:
                continue
        file.close()
        context.close()
        browser.close()

    def execute_by_custom(self, *args, **kwargs):
        pass

    @staticmethod
    def read_history_list():
        if os.path.exists(SCREENSHOT_HISTORY_PATH):
            with open(SCREENSHOT_HISTORY_PATH, 'r', encoding='utf-8') as file:
                lines = file.readlines()
            return [line.strip() for line in lines]
        return []

    @staticmethod
    def screenshot(url: str, page: Page, filename: str):
        page.goto(url)
        page.wait_for_load_state("load")
        time.sleep(SCREENSHOT_DELAY)
        page.mouse.wheel(0, 800)
        time.sleep(SCREENSHOT_DELAY)
        page.screenshot(path=os.path.join(base_path, SCREENSHOT_OUT_PATH.format(filename)))
