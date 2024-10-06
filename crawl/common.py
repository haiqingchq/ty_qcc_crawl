# -*- coding: utf-8 -*-
import os

import pandas as pd

from config import OPTION


def is_excel_file(file_path):
    """
    判断当前文件是否是一个excel文件
    :param file_path:
    :return:
    """
    excel_extensions = ['.xls', '.xlsx']
    return os.path.splitext(file_path)[1].lower() in excel_extensions


class ExcelHandler:
    """
        处理Excel文件的类
    """

    def __init__(self, excel_path):
        self.excel_path = excel_path
        self.df = pd.read_excel(excel_path)
        # 如果该程序运行的是这两个爬虫任务，就需要做这个检查
        if OPTION in [1, 2]:
            self.check_excel_file()

    def check_excel_file(self):
        """
        判断excel文件，文件格式是否存在问题，是否包含：借款人企业名称， 社会统一信用代码， 命名 这几个文件头
        :return:
        """
        required_columns = ['借款人企业名称', '社会统一信用代码', '命名'] if OPTION == 1 \
            else ['借款人企业名称', '社会统一信用代码']

        for column in required_columns:
            if column not in self.df.columns:
                raise ValueError(f"你指定的excel文件缺失以下文件头: {column}，请重新指定Excel文件，或者修改文件")

    def get_company_info_v1(self):
        """
            获取Excel文件中，的公司信息，包括公司名称和社会统一信用代码
        :return:
        """

        business_list = self.df['借款人企业名称']
        credit_list = self.df['社会统一信用代码']

        return business_list, credit_list

    def get_company_info_v2(self):
        business_list = self.df['借款人企业名称']
        credit_list = self.df['社会统一信用代码']
        filename_list = self.df['命名']

        return business_list, credit_list, filename_list

    # 将查询到的社会统一信用代码存入到Excel文件中
    def save_company_info(self, business_list, credit_list):
        """
            将查询到的社会信用统一代码更新到self.df中，最后将self.df输出到本地
            这里要指定文件的名字，但是
        :param business_list:
        :param credit_list:
        :return:
        """
        self.df.to_excel()

