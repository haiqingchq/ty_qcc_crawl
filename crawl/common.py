# -*- coding: utf-8 -*-
import os

import pandas as pd


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

    def get_company_info_v1(self):
        """
            获取Excel文件中，的公司信息，包括公司名称和社会统一信用代码
        :return:
        """

        df = pd.read_excel(self.excel_path
                           )

        business_list = df['借款人企业名称']
        credit_list = df['社会统一信用代码']

        return business_list, credit_list

    def get_company_info_v2(self):
        df = pd.read_excel(self.excel_path)

        business_list = df['借款人企业名称']
        credit_list = df['社会统一信用代码']
        filename_list = df['命名']

        return business_list, credit_list, filename_list

    # 将查询到的社会统一信用代码存入到Excel文件中
    def save_company_info(self, business_list, credit_list):
        """
            将查询到的社会统一信用代码存入到Excel文件中
        :param business_list:
        :param credit_list:
        :return:
        """

