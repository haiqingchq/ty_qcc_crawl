import os.path
from concurrent.futures import ThreadPoolExecutor

import pandas as pd
from playwright.sync_api import sync_playwright

from config import LOGIN_TAP
from config import UNDO_PATH, FILENAME
from crawl.base import Crawler


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
        self.ty_crawler.run(self.playwright)
        self.qcc_crawler.run(self.playwright)

    def start(self):
        """
        使用单线程模式启动爬虫项目
        :return:
        """
        self.login()
        self.start_crawlers()

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
            for _ in range(2):
                executor.submit(self.start_crawlers)

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
        from queue import Queue
        # 1、获取所有的公司列表
        all_companies = self.ty_crawler.excel_handler.get_all_companies()
        # 2、获取已经做完了
        history_companies = self.ty_crawler.read_history_list()
        # 3、获得到未作的
        undo_companies = list(set(all_companies) - set(history_companies))
        # 4、将未作的放到queue中
        undo_queue = Queue()
        for company in undo_companies:
            undo_queue.put(company)
        return undo_queue

