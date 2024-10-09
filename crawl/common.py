# -*- coding: utf-8 -*-
import os

import pandas as pd

from config import OPTION, BUSINESS_NAME, CREDIT_NAME, NAMED


def get_all_file_names(folder_path):
    file_names = []
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            file = file.replace(".png", "")
            file_names.append(file)
    return file_names


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

    def get_all_companies(self):
        """
        获得所有公司的名单
        :return:
        """
        return self.df[BUSINESS_NAME]

    def get_empty_credit_rows(self):
        """
        获取到
        :return:
        """
        empty_credit_rows = self.df[self.df[CREDIT_NAME].isnull()]
        return empty_credit_rows[BUSINESS_NAME].tolist()

    def get_info_by_company(self, company):
        """
        通过 公司名称，在 df 中获得一行数据
        :param company:
        :return: list
        """
        row = self.df[self.df[BUSINESS_NAME] == company].index[0]
        row_data = self.df.loc[row, [BUSINESS_NAME, CREDIT_NAME, NAMED]].tolist()
        return row_data

    def check_excel_file(self):
        """
        判断excel文件，文件格式是否存在问题，是否包含：借款人企业名称， 社会统一信用代码， 命名 这几个文件头
        :return:
        """
        required_columns = [BUSINESS_NAME, CREDIT_NAME, NAMED] if OPTION == 1 \
            else [BUSINESS_NAME, CREDIT_NAME]

        for column in required_columns:
            if column not in self.df.columns:
                raise ValueError(f"你指定的excel文件缺失以下文件头: {column}，请重新指定Excel文件，或者修改文件")

    def get_company_info_v1(self):
        """
            获取Excel文件中，的公司信息，包括公司名称和社会统一信用代码
        :return:
        """

        business_list = self.df[BUSINESS_NAME]
        credit_list = self.df[CREDIT_NAME]

        return business_list, credit_list

    def get_company_info_v2(self):
        business_list = self.df[BUSINESS_NAME]
        credit_list = self.df[CREDIT_NAME]
        filename_list = self.df[NAMED]

        return business_list, credit_list, filename_list

    # 将查询到的社会统一信用代码存入到Excel文件中
    def save_company_info(self, target_dict: [str, str]):
        """
        :param target_dict:
        :return:
        """
        # 1、读取文件
        df = pd.read_excel(self.excel_path)
        # 2、将内容更新到文件中
        for business, credit in target_dict.items():
            index = df.loc[df[BUSINESS_NAME] == business].index[0]
            df.at[index, CREDIT_NAME] = credit

        # 3、将文件输出到指定位置
        df.to_excel(self.excel_path, index=False)
