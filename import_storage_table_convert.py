#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
   created     ： The Aug 07 12:18 PM 2021
   filename    ： import_coll_table_convert.py
   author      :  Leon
   email       :  silenceace@gmail.com
   Description : 表格提取库房信息转换为藏品柜架导入表格
   使用：python3 coll_import_table_covert.py '3' '/Users/potato/Desktop/n1'
   参数1：3 数据行开始的索引  参数2：要处理的表格文件夹路径

   其他说明：对应配置请从 config.json  execl_convert=>import_storage=>source_table_map=>进行映射配置
"""
__author__ = 'Leon'

import os, sys

from api_coll import ApiColl
from common import *
import shutil
import datetime
import xlrd
import openpyxl
from config import (global_config, execl_convert_set)
from common.util import (
    send_wechat
)

LOGGER_FILE_NAME = 'import_storage_table_convert.log'
logger = new_logger(LOGGER_FILE_NAME)
IMPORT_STORAGE_XLS_TPL_FILE = os.path.join(os.getcwd(), 'tml', 'xls_template', 'storage_import.xlsx')
IMPORT_STORAGE_XLS_TITLE_ARRAY = ['总登记号', '库房名称', '具体位置', '详细位置']

class StorageXlsConvert:
    def __init__(self, source_xls_path=None, export_xls_path=None, export_xls_max_count=1000,
                 source_xls_data_start_index=3):
        """
        :param source_xls_path: 待转换的藏品表格文件夹
        :param export_xls_path: 转换输出的表格文件夹
        :param export_xls_max_count: 输出的每个表格最大行数
        :param source_xls_data_start_index: 一普表格数据行开始行索引
        """
        if source_xls_path is None or len(source_xls_path) == 0:
            raise PException('请正确设置Execl表格文件夹路径')
        if not os.path.exists(source_xls_path):
            raise PException('Execl表格文件夹路径不存在')
        self.xls_list = util.search_files(root=source_xls_path, ext_list=['xls', 'xlsx'], deep_search=False)
        if len(self.xls_list) == 0:
            raise PException('该目录不存在导入的表格')
        if export_xls_path is None or len(export_xls_path) == 0 or not os.path.exists(export_xls_path):
            export_xls_path = os.path.join(source_xls_path, 'result')
            if not os.path.exists(export_xls_path):
                os.makedirs(export_xls_path)
        self.coll_api = ApiColl()
        self.session = self.coll_api.session_user
        self.mid = self.session['user']['mid']
        self.uid = self.session['user']['id']
        self._message = global_config.config['messenger'].getboolean('enable')
        self._jsd_key = global_config.get_raw('messenger', 'jsdkey')
        self.source_xls_path = source_xls_path
        self.export_xls_path = export_xls_path
        self.source_xls_data_start_index = source_xls_data_start_index
        self.export_xls_max_count = export_xls_max_count
        self.source_table_map = execl_convert_set['import_storage']['source_table_map']
        self.replace_storage_name_rules = execl_convert_set['import_storage']['replace_storage_name_rules']
        _db_storage_name_list = self.coll_api.storage_simple_list(self.mid)
        self.db_storage_name_list = [] if _db_storage_name_list is None else list(map(lambda v:v.get('name'), _db_storage_name_list))
        pass

    def config_desc(self):
        con_desc = "\n处理的表格文件夹：{}\n".format(self.source_xls_path)
        con_desc += "输出的表格文件夹：{}\n".format(self.export_xls_path)
        con_desc += "要转换的表格数：{}\n".format(len(self.xls_list))
        con_desc += "要转换的表格分别为：\n{}\n\n".format(
            '\n'.join(
                list(
                    map(lambda v: v['origin_name'], self.xls_list)
                )
            )
        )
        return con_desc
        pass

    @classmethod
    def show_option_start(cls):
        import_file_path = input("请输入要转换的源表格文件夹路径：")
        export_file_path = input("请输入转换输出表格文件夹路径(留空则和输入目录一致)：")
        source_xls_data_start_index = input("一普表格的数据行开始索引：")
        export_xls_max_count = input("输出的表格记录最大行数：")
        if source_xls_data_start_index is None or len(source_xls_data_start_index) == 0:
            source_xls_data_start_index = '1'
        if export_xls_max_count is None or len(export_xls_max_count) == 0:
            export_xls_max_count = '500'

        cls(import_file_path, export_file_path, int(export_xls_max_count),
            int(source_xls_data_start_index)).direct_start()

    def convert_batch_coll_import_xls(self, xls_file):
        xls_book = xlrd.open_workbook(xls_file['full_path'])
        xls_sheet = xls_book.sheet_by_index(0)
        logger.info("%s %s=> 数据行数：%s 数据列数：%s。", xls_file['desc'], xls_sheet.name,
                                                      xls_sheet.nrows - self.source_xls_data_start_index,
                                                      xls_sheet.ncols)

        xls_data_count = xls_sheet.nrows - self.source_xls_data_start_index
        export_xls_list = []
        cur_storage_xls = dict()
        storage_name_set = set()
        for rx in range(xls_data_count):
            # 通用映射读取数据行
            _row_data = xls_sheet.row(self.source_xls_data_start_index + rx)
            row_map_data = dict()
            for map_key in self.source_table_map.keys():
                _source_index = self.source_table_map.get(map_key)
                if _source_index == -1 or _source_index > len(_row_data) - 1:
                    continue
                _col_val = _row_data[_source_index]
                row_map_data[map_key] = _col_val.value if _col_val is not None else None

            if rx % self.export_xls_max_count == 0:
                if 'path' in cur_storage_xls.keys():
                    cur_storage_xls['book'].save(cur_storage_xls['path'])
                cur_storage_xls['path'] = os.path.join(self.export_xls_path, '柜架导入{}_{}_{}{}.xlsx'.format(
                    '_{}'.format(len(export_xls_list) + 1) if self.export_xls_max_count < xls_data_count else '',
                    xls_file['name'], xls_data_count, '_start_{}'.format(rx) if self.export_xls_max_count < xls_data_count else ''))
                export_xls_list.append(cur_storage_xls['path'])
                shutil.copy(IMPORT_STORAGE_XLS_TPL_FILE, cur_storage_xls['path'])
                cur_storage_xls['book'] = openpyxl.load_workbook(cur_storage_xls['path'])
                cur_storage_xls['sheet'] = cur_storage_xls['book'].worksheets[0]
                logger.info("%s输出表格：%s", xls_file['desc'], cur_storage_xls['path'])
            if rx % self.export_xls_max_count < self.export_xls_max_count:
                cur_coll_row_data = []
                for _key in IMPORT_STORAGE_XLS_TITLE_ARRAY:
                    _value = row_map_data[_key] if _key in row_map_data.keys() else ''
                    if _key == '库房名称':
                        if _value is not None and type(_value) is str and len(_value) > 0 and len(self.replace_storage_name_rules) > 0: # 根据替换实时替换库房名称
                            for _rule in self.replace_storage_name_rules: _value = _value.replace(_rule.split('$$')[0], _rule.split('$$')[1])
                        elif _value is None or len(_value) == 0:
                            _value = '其他'
                        storage_name_set.add(_value)
                    cur_coll_row_data.append(_value)
                cur_storage_xls['sheet'].append(cur_coll_row_data)
                if rx == (xls_sheet.nrows - self.source_xls_data_start_index - 1):
                    cur_storage_xls['book'].save(cur_storage_xls['path'])

        logger.info('%s, 库房名称含：【%s】', xls_file['desc'], ' '.join(list(storage_name_set)))

        return dict(xls_list=list(map(lambda v: util.file_info(v), export_xls_list)), storage_name_list = list(storage_name_set))
        pass

    def direct_start(self):
        logger.info("配置信息：%s", self.config_desc())

        total_xls_count = len(self.xls_list)
        export_table_count = 0
        task_start_time = datetime.datetime.now()
        fail_xls_name_list = []  # 转换失败的表格
        storage_name_set = set()

        for i, _one_file in enumerate(self.xls_list):
            desc = '序号.{0}/{1}【{2}】'.format(str(i + 1), total_xls_count, _one_file['origin_name'])
            start_time = datetime.datetime.now()
            logger.info("%s 转换中..", desc)
            _one_file['desc'] = desc
            converted_rlt = self.convert_batch_coll_import_xls(_one_file)

            end_time = datetime.datetime.now()
            elapsed_sec = (end_time - start_time).seconds
            desc += "转换耗时：{} 秒".format(elapsed_sec)

            if converted_rlt is None:
                logger.error("%s转换表格遇到错误。表格路径：%s", desc, _one_file['full_path'])
                fail_xls_name_list.append(_one_file['origin_name'])
                shutil.copy(_one_file.get('full_path'),
                            os.path.join(self.export_xls_path, _one_file.get('origin_name')))
                continue
            export_table_count += len(converted_rlt['xls_list'])
            for _name in converted_rlt['storage_name_list']: storage_name_set.add(_name)

            logger.info("%s，输出了 %s 个表格，分别是：%s。", desc, len(converted_rlt['xls_list']),
                        '、'.join(list(map(lambda v: v['origin_name'], converted_rlt['xls_list']))))
        task_end_time = datetime.datetime.now()
        task_elapsed_sec = (task_end_time - task_start_time).seconds

        # logger.info('\n\n出现的库房名称 %s 个,包含：%s', len(storage_name_set), '\n'.join(list(storage_name_set)))
        no_db_storage_name_list = list(filter(lambda  v: v not in self.db_storage_name_list, list(storage_name_set)))
        logger.info('\n\n系统不包含的库房名称 %s 个,分别是：\n%s', len(no_db_storage_name_list), '\n'.join(no_db_storage_name_list))

        summary = "处理表格文件夹: {}, 共处理 {} 个表格，输出了 {} 个表格({})。\n任务开始于：{}，总耗时：{} 秒。  \n转换失败的表格是：{}。".format(
            self.source_xls_path,
            len(self.xls_list),
            export_table_count,
            self.export_xls_path,
            task_start_time,
            task_elapsed_sec,
            '无' if len(
                fail_xls_name_list) == 0 else
            '、'.join(
                fail_xls_name_list))
        logger.info('\n\n' + summary)
        if self._message:
            send_wechat(self._jsd_key, "表格转换完成。", summary)


if __name__ == '__main__':
    source_xls_data_start_index = sys.argv[1]
    xls_path = sys.argv[2]
    StorageXlsConvert(xls_path, export_xls_path=None,  export_xls_max_count=1000, source_xls_data_start_index=int(source_xls_data_start_index)).direct_start()
    # StorageXlsConvert('/Users/potato/Desktop/n1', export_xls_max_count=1000, export_xls_path=None, source_xls_data_start_index=3).direct_start()
