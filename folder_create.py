#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
   created     ： The Feb 02 4:29 PM 2021
   filename    ： folder_create.py
   author      :  Leon
   email       :  silenceace@gmail.com
   Description :  根据execl表格藏品信息创建目录列表。其中目录列表的子目录 可在 tml/folder_create/sub_dir_tml 进行创建和修改
"""
__author__ = 'Leon'

import os
import shutil
from common import (new_logger, PException, ExeclUtil)

logger = new_logger('folder_create.log')
DEF_SUB_DIR_TML_PATH = os.path.join(os.getcwd(), 'tml', 'folder_create', 'sub_dir_tml')


class FolderCreate:
    def __init__(self, xls_path=None, out_path=None, folder_name_format=None, dir_tml_path=None):
        """
        :param xls_path: 目录表格路径
        :param folder_name_format: 生成的目录格式，变量num、name  如格式为：1901_num_name
        :param out_path: 生成的目录所在的根目录
        :param dir_tml_path: 生成的目录子目录的模板结构
        """
        print(xls_path, out_path, folder_name_format, dir_tml_path)
        self.sheet_data = ExeclUtil.read_execl_data(xls_path)

        if dir_tml_path is None or len(dir_tml_path) == 0:
            dir_tml_path = DEF_SUB_DIR_TML_PATH
        if not os.path.exists(dir_tml_path):
            raise PException("模板目录结构不存在，请设置 {}".format(dir_tml_path))
        if out_path is None or len(out_path) == 0:
            out_path = os.path.split(xls_path)[0]
        if not os.path.exists(out_path):
            os.makedirs(out_path)
        if folder_name_format is None or len(folder_name_format) == 0:
            folder_name_format = 'num_name'

        self.out_path = out_path
        self.folder_name_format = folder_name_format
        self.dir_tml_path = dir_tml_path

    @classmethod
    def show_option_start(cls):
        print("根据execl表格藏品信息创建目录列表:")
        xls_path = input("目标表格所在路径（具体到文件名）：")
        out_path = input("输出的目标目录，目标目录必须为空（默认为：{}）：".format(os.path.split(xls_path)[0]))
        folder_name_format = input("生成的目录格式，变量num、name，如：2021_num_name（默认为:num_name）：")
        dir_tml_path = input("生成的目录包含的子目录结构，请设置模板目录路径，默认为{}：".format(DEF_SUB_DIR_TML_PATH))
        cls(xls_path, out_path, folder_name_format, dir_tml_path).direct_start()

    def direct_start(self):
        """
        直接开始执行
        """
        if self.sheet_data is None:
            logger.error('目标表格无数据，请检查')
            pass
        logger.info("开始生成目录，输出到：%s。", self.out_path)

        fail = 0
        for item in self.sheet_data:
            num = item.get('编号')
            name = item.get('名称')

            folder_name = self.folder_name_format.replace('num', '' if num is None else num). \
                replace('name', '' if name is None else name)
            folder_path = os.path.join(self.out_path, folder_name)

            if os.path.exists(folder_path):
                logger.error("%s 文件夹已存在，已跳过。", folder_name)
                fail += 1
            else:
                shutil.copytree(self.dir_tml_path, folder_path)
                logger.info("已生成目录：%s, 目录路径：%s", folder_name, folder_path)

        logger.info("目录生成完毕，共生成了 %s 个目录，失败 %s 个，输出到：%s。", len(self.sheet_data) - fail, fail, self.out_path)


if __name__ == '__main__':
    FolderCreate.show_option_start()
