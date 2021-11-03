#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
   created     ： The Feb 02 5:18 PM 2021
   filename    ： execlutil.py
   author      :  Leon
   email       :  silenceace@gmail.com
   Description :
"""
__author__ = 'Leon'

import os
import xlrd
from common import util
from common import PException


class ExeclUtil:
    def __init__(self):
        pass

    @classmethod
    def workbook_from_execl_file(cls, xls_path):
        """
        检查并获取Execl book对象
        :param xls_path: 表格完整路径
        :return: 无返回，如果错误则抛出错误
        """
        if xls_path is None or not os.path.exists(xls_path) or not os.path.isfile(xls_path):
            raise PException('请提供源数据表格路径供读取')
        file_info = util.file_info(xls_path)
        if file_info['ext'] not in ('xls', 'xlsx'):
            raise PException('非表格文件，请提供正确的表格文件路径')
        try:
            return xlrd.open_workbook(xls_path)
        except Exception as err:
            raise err

    @classmethod
    def execl_info(cls, xls_path):
        book = cls.workbook_from_execl_file(xls_path)
        return dict(sheet_count=book.nsheets, sheet_names=book.sheet_names(),
                    sheets=list(map(lambda v: book.sheet_by_name(v), book.sheet_names)))

    def get_sheet(self, book, which_sheet):
        """
        获取对应的sheet对象
        :param book: execl book对象
        :param which_sheet: 根据name或int获取
        :return:
        """
        if which_sheet is None:
            sheet = book.sheet_by_index(0)
        elif type(which_sheet) == str:
            sheet = book.sheet_by_name(which_sheet)
        else:
            sheet = book.sheet_by_index(which_sheet)
        return sheet

    def get_sheet_titles(self, sheet):
        """
        获取表格标题集合
        """
        return list(map(lambda x: x.value, sheet.row(0)))

    @classmethod
    def read_execl_data(cls, xls_path, which_sheet=None, data_start_row_index=None):
        """
        读取execl表格
        :param which_sheet: 根据name或int获取对应的sheet
        :param xls_path: 表格路径(表格必须有标题列)
        :param data_start_row_index: 数据开始行索引，一般为第二行:1,第一行为标题行
        :return: 返回dict集合，字典名称为表格第一行标题
        """
        if data_start_row_index is None:
            data_start_row_index = 1
        if which_sheet is None:
            which_sheet = 0
        list = []

        book = cls().workbook_from_execl_file(xls_path)
        sheet = cls().get_sheet(book, which_sheet)
        titles = cls().get_sheet_titles(sheet)

        for idx in range(sheet.nrows):
            if idx < data_start_row_index: continue
            row_info = dict()
            for col_idx, title in enumerate(titles):
                row_info[title] = sheet.cell_value(rowx=idx, colx=col_idx)
            list.append(row_info)
        return list
        pass
