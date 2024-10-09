import os.path
from concurrent.futures import ThreadPoolExecutor

import pandas as pd
from playwright.sync_api import sync_playwright

from config import LOGIN_TAP, CREDIT_UNDO_QUEUE
from config import SCREENSHOT_OUT_DIR, NAMED, BUSINESS_NAME, SCREENSHOT_HISTORY_PATH
from config import UNDO_PATH, FILENAME
from crawl.base import Crawler
from crawl.common import get_all_file_names


class Actuator:
    """
        执行器，处理调度逻辑的
    """

    def __init__(self, ty_crawler: Crawler, qcc_crawler: Crawler):
        """
        面向接口编程，采用依赖注入的方式，增加程序的可扩展性
        :param ty_crawler:
        :param qcc_crawler:
        """
        self.ty_crawler = ty_crawler
        self.qcc_crawler = qcc_crawler
        self.playwright = sync_playwright().start()
        self.get_undo_companies_list()

    @staticmethod
    def write_history(excel_path: str):
        df = pd.read_excel(excel_path)
        all_files = get_all_file_names(SCREENSHOT_OUT_DIR)
        history_list = []
        for file_name in all_files:
            business = df[df[NAMED] == file_name][BUSINESS_NAME].tolist()[0]
            history_list.append(business)
        file = open(SCREENSHOT_HISTORY_PATH, 'w', encoding='utf-8')
        for history_item in history_list:
            file.write(f"{history_item}\n")
        file.close()

    def login(self):
        print("\033[91m正在检查登录状态信息，请稍等...")
        # 登录之前进行登录状态的检查
        self.ty_crawler.check_login(self.playwright)
        self.qcc_crawler.check_login(self.playwright)

        if LOGIN_TAP == "QRCODE":
            self.ty_crawler.login(self.playwright)
            self.qcc_crawler.login(self.playwright)
        elif LOGIN_TAP == "PASSWORD":
            self.ty_crawler.login_by_password(self.playwright)
            self.qcc_crawler.login_by_password(self.playwright)
        print("\033[91m登录信息验证通过...")

    def start_crawlers(self):
        print("任务已启动，正在爬取任务……")
        self.ty_crawler.run()
        self.qcc_crawler.run()

    def start(self):
        """
        使用单线程模式启动爬虫项目
        :return:
        """
        self.login()
        self.start_crawlers()

    def thread_start_crawlers(self, thread_num):
        self.ty_crawler.thread_run()
        self.qcc_crawler.thread_run()

    def thread_start(self):
        """
        这里是使用多线程模式启动爬虫项目
        需要解决的问题：
            1、什么任务是没做的，什么任务是做了的。
            2、多个线程如何避免重复执行相同的代码

        :return:
        """
        self.login()
        with ThreadPoolExecutor() as executor:
            # for _ in range(3):
            #     executor.submit(self.thread_start_crawlers)
            executor.map(self.ty_crawler.thread_run, range(3))

        with ThreadPoolExecutor() as executor:
            executor.map(self.qcc_crawler.thread_run, range(3))

    def close(self):
        self.playwright.stop()

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
            对象释放的时候自动执行close函数，释放资源
        :param exc_type:
        :param exc_val:
        :param exc_tb:
        :return:
        """
        self.close()

    def check_un_crawled_companies(self, excel_path: str):
        """
            检查未完成爬取公司的名单，将其写入到undo文件中，方便后续跟进
            在爬取完成之后调用
        :return:
        """
        # 1、已经完成爬取的名单
        completed_list = self.ty_crawler.read_history_list()
        # 2、所有需要爬取公司的名单
        df = pd.read_excel(excel_path)
        all_companies = df['借款人企业名称'].to_list()
        # 3、获取到没有完成爬取公司的名单
        uncompleted_companies = list(set(all_companies) - set(completed_list))

        # 4、创建指定文件夹，文件名

        filename = os.path.join(UNDO_PATH, FILENAME)

        # 5、将未完成爬取的名单写入到文件中便于后续跟进
        with open(f'{filename}.txt', 'w', encoding='utf-8') as f:
            for company in uncompleted_companies:
                f.write(f'{company}\n')

    def get_undo_companies_list(self):
        """

        :return:
        """
        for company in self.ty_crawler.excel_handler.get_empty_credit_rows():
            CREDIT_UNDO_QUEUE.put(company)
        CREDIT_UNDO_QUEUE.put(0)
        print(f"本次任务总量: {CREDIT_UNDO_QUEUE.qsize()}")
        return CREDIT_UNDO_QUEUE
