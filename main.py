# -*- coding: utf-8 -*-
import os
import time

from config import CURRENT_ERR_PATH, OPTION, CREDIT_DO_QUEUE
from config import MAX_ATTEMPTS, ATTEMPT_DELAY
from crawl.cmd import Actuator
from crawl.common import is_excel_file
from crawl.qcc import QCCCreditCrawl, QCCScreenshotCrawl
from crawl.ty import TyCreditCrawl, TYScreenshotCrawl


def main():
    start_time = time.time()
    max_attempts = MAX_ATTEMPTS
    attempt_delay = ATTEMPT_DELAY

    err_file = open(CURRENT_ERR_PATH + '.log', 'w', encoding='utf-8')

    while True:
        excel_path = input("\033[91m请输入excel文件的路径：")
        if not excel_path.endswith('.xlsx') or not excel_path.endswith('.xls'):
            excel_path = excel_path + '.xlsx'

        if os.path.exists(excel_path) and os.path.isfile(excel_path) and is_excel_file(excel_path):
            break
        else:
            print("\033[91m输入的文件路径不合法，请你重新输入：")

    if OPTION == 1:
        ty_crawler = TYScreenshotCrawl(excel_path=excel_path)
        qcc_crawler = QCCScreenshotCrawl(excel_path=excel_path)
    else:
        ty_crawler = TyCreditCrawl(excel_path=excel_path)
        qcc_crawler = QCCCreditCrawl(excel_path=excel_path)
    actuator = Actuator(ty_crawler=ty_crawler, qcc_crawler=qcc_crawler)

    attempts = 0
    try:
        while attempts < max_attempts:
            try:
                actuator.thread_start()
                break  # If the start method completes successfully, exit the loop
            except Exception as e:
                attempts += 1
                print(f"\033[91m启动任务时发生错误，第{attempts}次尝试重启：{e}")
                err_file.write(str(e))
                time.sleep(attempt_delay)

    finally:
        # 在整个程序结束之后，再检测是否没有爬取成功的公司，写入到文件中
        if OPTION == 1:
            actuator.write_history(excel_path=excel_path)
            # 只有在进行截图爬取的时候才需要进行这个操作，因为社会信用统一代码可以直接通过查看文件就能看到未完成的公司信息
            actuator.check_un_crawled_companies(excel_path=excel_path)
        if attempts == max_attempts:
            print("\033[91m达到最大尝试次数，任务无法启动")
        ty_crawler.excel_handler.save_company_info(CREDIT_DO_QUEUE)
        end_time = time.time()
        time_taken = end_time - start_time
        print(f'\033[91m共耗时：{time_taken:.1f}秒({time_taken / 60:.1f}分钟)')


if __name__ == "__main__":
    main()

