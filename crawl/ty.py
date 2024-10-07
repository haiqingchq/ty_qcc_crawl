# -*- coding: utf-8 -*-
import os.path
import re
import sys
import time

from playwright.sync_api import Page
from playwright.sync_api import Playwright

from config import User_Agent, Disable_Blink_Features
from config import ty_cookie_path, ty_login_url, ty_search_url, ty_search_target, DELAY, ty_username, ty_password
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
        bs = playwright.chromium.launch(headless=False)
        if os.path.exists(self.cookie_path):
            ctx = bs.new_context(storage_state=self.cookie_path)
            page = ctx.new_page()
            # 2、如果存在就尝试进入这个主页
            page.goto(ty_search_url)
            # 3、进入主页之后，首先要判断这个登录状态是否失效
            page.wait_for_load_state("load")
            time.sleep(DELAY)  # 页面加载需要时间，加载完成就定位元素，会导致没有定位到元素直接进入未登录得分支
            content = page.query_selector_all("text='登录/注册'")
            if content:
                # 4、如果存在，就说明登录状态已经失效了，需要重新登录
                page.goto(ty_login_url)
                # 5、输入账号密码登录一下
                page.locator(".toggle_box.-qrcode").click()
                page.query_selector_all("text='密码登录'")[0].click()
                page.locator("#mobile").fill(ty_username)
                page.locator("#password").fill(ty_password)

                # 6、等待登录成功
                page.wait_for_url(ty_search_url)
                ctx.storage_state(path=self.cookie_path)
        else:
            ctx = bs.new_context()
            page = ctx.new_page()
            # 4、如果存在，就说明登录状态已经失效了，需要重新登录
            page.goto(ty_login_url)
            # 5、等待用户扫描二维码登录
            page.locator(".toggle_box.-qrcode").click()
            page.query_selector_all("text='密码登录'")[0].click()
            page.locator("#mobile").fill("17773059673")
            page.locator("#password").fill("chq20030306")
            # 6、等待登录成功
            page.wait_for_url(ty_search_url)
            page.context.storage_state(path=self.cookie_path)
        if page.query_selector_all('text="登录/注册"'):
            print("天眼登录失败，请重新运行程序并扫码")
            os.remove(self.cookie_path)
            sys.exit()
        page.close()
        ctx.close()
        bs.close()

    def get_credit_from_page(self, page: Page, url: str):
        page.goto(url)
        page.wait_for_load_state("load")
        target = page.query_selector("tbody").query_selector_all("tr")[3].query_selector_all('td')[1].text_content()
        print(target)


class TyCreditCrawl(CreditCrawl, TYCrawlerBase):
    def get_credit_from_page(self, page: Page, url: str):
        page.goto(url)
        page.wait_for_load_state("load")
        target = page.query_selector("tbody").query_selector_all("tr")[3].query_selector_all('td')[1].text_content()
        return target

    def execute_by_custom(self, page: Page, keyword: str, *args, **kwargs):
        """已经登录"""
        # 1、尝试进入搜索页面
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
        # 3、跳转链接，并截图
        if match:
            next_url = match.group()
            credit = self.get_credit_from_page(url=next_url, page=page)
            return credit
        else:
            # 在天眼中没有找到该企业
            raise AttributeError


class TYScreenshotCrawl(ScreenshotCrawl, TYCrawlerBase):
    def execute_by_custom(self, page: Page, keyword: str, filename: str, *args, **kwargs):
        """已经登录"""
        # 1、尝试进入搜索页面
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
        # 3、跳转链接，并截图
        if match:
            next_url = match.group()
            self.screenshot(url=next_url, page=page, filename=filename)
        else:
            # 在天眼中没有找到该企业
            raise AttributeError
