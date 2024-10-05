# -*- coding: utf-8 -*-
"""
    企查查非VIP用户是有访问次数限制的，如果单次访问量非常大的话，还是得用vip用户进行登录
"""
import os.path
import re
import sys
import time

from playwright.sync_api import Page
from playwright.sync_api import Playwright

from config import User_Agent, Disable_Blink_Features
from config import qcc_cookie_path, qcc_search_url, qcc_login_url, qcc_login_target_url, qcc_search_target, DELAY
from crawl.base import Crawler, CreditCrawl, ScreenshotCrawl
from crawl.common import ExcelHandler


class QCCCrawlerBase(Crawler):

    def __init__(self, excel_path: str):
        self.excel_handler = ExcelHandler(excel_path)
        self.cookie_path = qcc_cookie_path

    def check_login(self, playwright: Playwright):
        if os.path.exists(self.cookie_path):
            bs = playwright.chromium.launch(headless=True, args=[f'--disable-blink-features={Disable_Blink_Features}',
                                                                 f'--user-agent={User_Agent}'])
            ctx = bs.new_context(storage_state=self.cookie_path)
            page = ctx.new_page()

            # 尝试进入到搜索页面中，获取 登录/注册 字样
            page.goto(qcc_search_url)
            page.wait_for_load_state("load")
            time.sleep(DELAY)
            if page.locator(".close").is_visible():
                page.locator(".close").click()
            content = page.query_selector_all("text='登录/注册'")

            if content:
                self.login_flag = False
            else:
                self.login_flag = True
        else:
            self.login_flag = False

    def login(self, playwright: Playwright):
        """
        保存登录状态
        :param playwright:
        :return:
        """
        if self.login_flag:
            return
        else:
            bs = playwright.chromium.launch(headless=False, args=[f'--disable-blink-features={Disable_Blink_Features}',
                                                                  f'--user-agent={User_Agent}'])
            ctx = bs.new_context()
            page = ctx.new_page()

            page.goto(qcc_login_url)
            page.wait_for_url(qcc_login_target_url)
            page.context.storage_state(path=self.cookie_path)

        page.close()
        ctx.close()
        bs.close()

    def login_by_password(self, playwright: Playwright):
        """
            该登录方式暂时不可用，在开发阶段
        :param playwright:
        :return:
        """
        bs = playwright.chromium.launch(headless=False)
        if os.path.exists(self.cookie_path):
            ctx = bs.new_context(storage_state=self.cookie_path)
            page = ctx.new_page()
            # 2、如果存在就尝试进入这个主页
            page.goto(qcc_search_url)
            page.wait_for_load_state("load")
            time.sleep(DELAY)  # 页面加载需要时间，加载完成就定位元素，会导致没有定位到元素直接进入未登录得分支
            if page.locator(".close").is_visible():
                page.locator(".close").click()
            # 3、进入主页之后，首先要判断这个登录状态是否失效
            content = page.query_selector_all("text='登录/注册'")
            if content:
                # 4、如果存在，就说明登录状态已经失效了，需要重新登录
                page.goto(qcc_login_url)
                page.locator(".login-change").click()
                page.query_selector_all('text="密码登录"')[0].click()
                page.locator('input[name="phone-number"').fill("17773059673")
                page.locator('input[name="password"').fill("chq20030306")
                page.wait_for_url(qcc_login_target_url)
                page.context.storage_state(path=self.cookie_path)
        else:
            ctx = bs.new_context()
            page = ctx.new_page()
            # 4、如果存在，就说明登录状态已经失效了，需要重新登录
            page.goto(qcc_login_url)
            page.locator(".login-change").last.click()
            page.locator(".login-tab").last.click()
            page.locator('div.password-login_wrapper input[name="phone-number"]').first.fill("17773059673")
            page.locator('div.password-login_wrapper input[name="password"]').first.fill("chq20030306")
            page.wait_for_url(qcc_login_target_url)
            page.context.storage_state(path=self.cookie_path)
        if page.query_selector_all('text="登录/注册"'):
            print("企查查登录失败，请重新运行程序并扫码")
            os.remove(self.cookie_path)
            sys.exit()

        page.close()
        ctx.close()
        bs.close()


class QCCCreditCrawl(CreditCrawl, QCCCrawlerBase):
    def get_credit_from_page(self, page: Page, url: str):
        page.goto(url)
        page.wait_for_load_state("load")
        credit = page.query_selector("table").query_selector_all("tr")[0].query_selector_all("td")[1].text_content()
        credit = credit.replace("复制", "")
        print(credit)

    def execute_by_custom(self, page: Page, keyword: str, *args, **kwargs):
        """已经登录"""
        # 1、进入到搜索页面
        page.goto(qcc_search_url)
        page.wait_for_load_state("load")

        # 2、可能跳出弹窗，如果跳出来的话，就关掉
        if page.locator(".modal-close.campaign.aicon.qccdicon.icon-icon_guanbixx").is_visible():
            page.locator(".modal-close.campaign.aicon.qccdicon.icon-icon_guanbixx").click()

        # 3、在输入框中输入指定要搜索的内容
        page.locator('#searchKey').click()
        page.locator('#searchKey').fill(keyword)
        page.locator('#searchKey').press("Enter")
        page.wait_for_load_state("load")
        time.sleep(DELAY)

        # 4、在页面中获取到我们需要的截图的链接
        html = page.content()
        pattern = re.compile(qcc_search_target)
        match = pattern.search(html)
        if match:
            next_url = match.group()
            self.get_credit_from_page(page=page, url=next_url)
        else:
            # 在企查查中没有找到该企业
            raise AttributeError


class QCCScreenshotCrawl(ScreenshotCrawl, QCCCrawlerBase):
    def execute_by_custom(self, page: Page, keyword: str, filename: str, *args, **kwargs):
        """已经登录"""
        # 1、进入到搜索页面
        page.goto(qcc_search_url)
        page.wait_for_load_state("load")

        # 2、可能跳出弹窗，如果跳出来的话，就关掉
        if page.locator(".modal-close.campaign.aicon.qccdicon.icon-icon_guanbixx").is_visible():
            page.locator(".modal-close.campaign.aicon.qccdicon.icon-icon_guanbixx").click()

        # 3、在输入框中输入指定要搜索的内容
        page.locator('#searchKey').click()
        page.locator('#searchKey').fill(keyword)
        page.locator('#searchKey').press("Enter")
        page.wait_for_load_state("load")
        time.sleep(DELAY)

        # 4、在页面中获取到我们需要的截图的链接
        html = page.content()
        pattern = re.compile(qcc_search_target)
        match = pattern.search(html)
        if match:
            next_url = match.group()
            self.screenshot(url=next_url, page=page, filename=filename)
        else:
            # 在企查查中没有找到该企业
            raise AttributeError
