# -*- coding: utf-8 -*-
import os.path
import re
import time

from playwright.sync_api import Page
from playwright.sync_api import Playwright

from config import User_Agent, Disable_Blink_Features
from config import ty_cookie_path, ty_login_url, ty_search_url, ty_search_target, DELAY, TY_USERNAME, TY_PASSWORD
from crawl.base import Crawler, CreditCrawl, ScreenshotCrawl
from crawl.common import ExcelHandler


class TYCrawlerBase(Crawler):
    cookie_path = ty_cookie_path

    def __init__(self, excel_path):
        self.excel_handler = ExcelHandler(excel_path)

    def check_login(self, playwright: Playwright):
        """
            这个函数用来检查当前是否处于登录状态
        :return: 登录成功就返回True，否则返回False
        """

        bs = playwright.chromium.launch(headless=True, args=[f'--disable-blink-features={Disable_Blink_Features}',
                                                             f'--user-agent={User_Agent}'])

        if os.path.exists(self.cookie_path):
            ctx = bs.new_context(storage_state=self.cookie_path)
            page = ctx.new_page()
            page.add_init_script(self.stealth_js)

            page.goto(ty_search_url)
            page.wait_for_load_state("load")
            time.sleep(DELAY)

            content = page.query_selector_all("text='登录/注册'")
            if content:
                self.login_flag = False
            else:
                self.login_flag = True
        else:
            self.login_flag = False

    def login(self, playwright: Playwright):
        """单独做一个登录检查的功能"""
        # 1、首先判断state.json文件是否存在
        if self.login_flag:
            return
        else:
            bs = playwright.chromium.launch(headless=False, args=[f'--disable-blink-features={Disable_Blink_Features}',
                                                                  f'--user-agent={User_Agent}'])
            ctx = bs.new_context()
            page = ctx.new_page()
            page.add_init_script(self.stealth_js)
            page.goto(ty_login_url)
            page.wait_for_url(ty_search_url)
            page.context.storage_state(path=self.cookie_path)

        page.close()
        ctx.close()
        bs.close()

    def login_by_password(self, playwright: Playwright):
        """做一个使用账号密码登录的功能"""
        # 1、首先判断state.json文件是否存在
        if self.login_flag:
            return
        else:
            bs = playwright.chromium.launch(headless=False)
            ctx = bs.new_context()
            page = ctx.new_page()
            # 4、如果存在，就说明登录状态已经失效了，需要重新登录
            page.goto(ty_login_url)
            # 5、等待用户扫描二维码登录
            page.locator(".toggle_box.-qrcode").click()
            page.query_selector_all("text='密码登录'")[0].click()
            page.locator("#mobile").fill(TY_USERNAME)
            page.locator("#password").fill(TY_PASSWORD)
            # 6、等待登录成功
            page.wait_for_url(ty_search_url)
            page.context.storage_state(path=self.cookie_path)

            page.close()
            ctx.close()
            bs.close()

    def search_and_get_url(self, page: Page, keyword: str):
        """
        跳转进入到搜索页面，搜索指定关键词，然后在搜索结果中获得目标url
        :param page:
        :param keyword: 需要搜索的关键词
        :return:
        """
        page.goto(ty_search_url)
        page.wait_for_load_state("load")

        # 2、搜索指定内容
        page.get_by_placeholder("请输入公司名称、老板姓名、品牌名称等").click()
        page.get_by_placeholder("请输入公司名称、老板姓名、品牌名称等").fill(keyword)
        page.get_by_placeholder("请输入公司名称、老板姓名、品牌名称等").press("Enter")
        page.wait_for_load_state("load")
        time.sleep(DELAY)

        html = page.content()
        pattern = re.compile(ty_search_target)
        match = pattern.search(html)
        if match:
            return match.group()
        else:
            raise AttributeError


class TyCreditCrawl(CreditCrawl, TYCrawlerBase):
    def get_credit_from_page(self, page: Page, url: str):
        page.goto(url)
        page.wait_for_load_state("load")
        # 获取到tbody
        tbody = page.query_selector("tbody")
        # 获取到这个tbody下面有多少个tr
        num_trs = len(tbody.query_selector_all("tr"))

        """
            这里工商信息的表格存在一些差异，所以这里需要针对表格的差异做出不同的提取操作
        """
        if num_trs == 10:
            target = tbody.query_selector_all("tr")[3].query_selector_all('td')[1].text_content()
        else:
            target = tbody.query_selector_all("tr")[4].query_selector_all('td')[1].text_content()
        return target

    def execute_by_custom(self, page: Page, keyword: str, *args, **kwargs):
        """已经登录"""
        # 1、尝试进入搜索页面
        next_url = self.search_and_get_url(page=page, keyword=keyword)
        # 3、跳转链接，并截图
        credit = self.get_credit_from_page(url=next_url, page=page)
        return credit


class TYScreenshotCrawl(ScreenshotCrawl, TYCrawlerBase):
    def execute_by_custom(self, page: Page, keyword: str, filename: str, *args, **kwargs):
        """已经登录"""
        next_url = self.search_and_get_url(page=page, keyword=keyword)
        # 3、跳转链接，并截图
        self.screenshot(url=next_url, page=page, filename=filename)
