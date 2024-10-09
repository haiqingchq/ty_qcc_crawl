import os
import time
from abc import ABC, abstractmethod

import pandas as pd
from playwright.sync_api import Page
from playwright.sync_api import Playwright
from playwright.sync_api import sync_playwright
from tqdm import tqdm

from config import MIN_JS_PATH, HEADLESS, Disable_Blink_Features, User_Agent
from config import SCREENSHOT_HISTORY_PATH, CREDITS_HISTORY_PATH, base_path, SCREENSHOT_OUT_PATH, SCREENSHOT_DELAY
from config import UNDO_QUEUE
from crawl.common import ExcelHandler

"""
    https://bot.sannysoft.com/
    这个网站可以检测浏览器的属性是否正常
"""


class StartInterface(ABC):
    @abstractmethod
    def run(self):
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

    def init_page(self):
        """
        初始化一个携带登录状态信息的page
        :return:
        """
        playwright = sync_playwright().start()
        bs = playwright.chromium.launch(headless=HEADLESS, args=[f'--disable-blink-features={Disable_Blink_Features}',
                                                                 f'--user-agent={User_Agent}'])
        ctx = bs.new_context(storage_state=self.cookie_path)
        pg = ctx.new_page()
        pg.add_init_script(self.stealth_js)
        return pg, bs, ctx

    def run(self):
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
    def run(self):
        page, browser, context = self.init_page()
        history_list = self.read_history_list()
        file = open(CREDITS_HISTORY_PATH, 'a', encoding='utf-8')

        business_list, credit_list = self.excel_handler.get_company_info_v1()
        target_dict = {}
        # 这里嵌套了两个try，主要是为了在执行过程中报错，可以将已经查询到的结果落盘，防止白做
        try:
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
        finally:
            self.excel_handler.save_company_info(target_dict=target_dict)
        file.close()
        context.close()
        browser.close()

    def thread_run(self):
        """
        多线程启动
        :return:
        """
        file = open(CREDITS_HISTORY_PATH, 'a', encoding='utf-8')
        page, browser, context = self.init_page()
        count = 0
        while not UNDO_QUEUE.empty():
            if count == 15:
                count = 0
                time.sleep(5)
            count += 1

            company = UNDO_QUEUE.get()
            info_list = self.excel_handler.get_info_by_company(company=company)
            business, credit = info_list[0], info_list[1]
            try:
                credit = self.execute_by_custom(keyword=business, page=page)
                print(credit)
                file.write(f"{company}\n")
            except AttributeError as e:
                # 当出现这个错误的时候，说明在当前的网站中没有查到这个公司，需要重新加入到队列中
                UNDO_QUEUE.put(company)
                continue
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
    def run(self):
        page, browser, context = self.init_page()
        history_list = self.read_history_list()

        business_list, credit_list, filename_list = self.excel_handler.get_company_info_v2()

        for business, credit, filename in tqdm(zip(business_list, credit_list, filename_list), desc="当前进度",
                                               unit="file", total=len(business_list)):
            if business not in history_list:
                try:
                    if not pd.isna(business):
                        self.execute_by_custom(keyword=business, page=page, filename=filename)
                    else:
                        self.execute_by_custom(keyword=credit, page=page, filename=filename)
                except AttributeError as e:
                    """
                        出现这个错误的情况有两种：
                            1、出现了访问的限制，导致没有进入到指定的页面
                            2、在qcc中不存在这家公司
                    """
                    continue
            else:
                continue
        context.close()
        browser.close()

    def thread_run(self):
        """
        多线程启动
        :return:
        """
        page, browser, context = self.init_page()
        history_list = self.read_history_list()
        count = 0
        while not UNDO_QUEUE.empty():
            # 每执行15次的时候休息5秒钟左右，防止被检测
            company = UNDO_QUEUE.get()
            if company in history_list:
                continue
            if count == 5:
                count = 0
                time.sleep(10)
            count += 1
            info_list = self.excel_handler.get_info_by_company(company=company)
            business, credit, filename = info_list[0], info_list[1], info_list[2]
            try:
                if business:
                    self.execute_by_custom(keyword=business, page=page, filename=filename)
                else:
                    self.execute_by_custom(keyword=credit, page=page, filename=filename)
            except AttributeError as e:
                # 当出现这个错误的时候，说明在当前的网站中没有查到这个公司，需要重新加入到队列中
                UNDO_QUEUE.put(company)
                continue

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
        # 增加操作：等待页面上面出现 工商信息 后，进行后续操作
        page.wait_for_url(url)
        page.mouse.wheel(0, 800)
        time.sleep(SCREENSHOT_DELAY)
        page.screenshot(path=str(os.path.join(base_path, SCREENSHOT_OUT_PATH.format(filename))))
