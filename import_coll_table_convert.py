#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
   created     ： The Aug 07 12:18 PM 2021
   filename    ： import_coll_table_convert.py
   author      :  Leon
   email       :  silenceace@gmail.com
   Description : 一普藏品表格转换为藏品批量导入表格
   使用：python3 import_coll_table_covert.py '3' '/Users/potato/Desktop/n1'
   参数1：3 数据行开始的索引  参数2：要处理的表格文件夹路径

   其他说明：一普的对应配置请从 config.json  execl_convert=>import_collection=>source_talbe_map=>进行映射配置
"""
__author__ = 'Leon'

import os, sys

from openpyxl.cell.cell import ILLEGAL_CHARACTERS_RE

from common import *
import shutil
import datetime
import xlrd
import openpyxl
from config import (global_config, execl_convert_set)
from common.util import (
    send_wechat
)

LOGGER_FILE_NAME = 'import_coll_table_convert.log'
logger = new_logger(LOGGER_FILE_NAME)
IMPORT_COLLECTION_XLS_TPL_FILE = os.path.join(os.getcwd(), 'tml', 'xls_template', 'collection_import.xlsx')
IMPORT_COLLECTION_XLS_TITLE_ARRAY = ['总登记号', '分类号', '原号', '入馆凭证号', '其他编号类型', '其他编号', '账册', '藏品名称', '曾用名', '类别', '年代',
                                     '具体年代', '材质', '级别',
                                     '完残程度', '实际数量', '尺寸单位', '通长', '通宽', '通高', '具体尺寸', '质量范围', '质量单位', '质量', '来源方式',
                                     '具体来源', '完残情况', '保护等级', '入藏时间范围', '入藏日期', '出土地', '著者', '版本', '存卷', '备注']


class CollXlsConvert:
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
        self._message = global_config.config['messenger'].getboolean('enable')
        self._jsd_key = global_config.get_raw('messenger', 'jsdkey')
        self.source_xls_path = source_xls_path
        self.export_xls_path = export_xls_path
        self.source_xls_data_start_index = source_xls_data_start_index
        self.export_xls_max_count = export_xls_max_count
        self.source_table_map = execl_convert_set['import_collection']['source_table_map']
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
        cur_coll_xls = dict()
        for rx in range(xls_data_count):
            # 通用映射读取数据行
            _row_data = xls_sheet.row(self.source_xls_data_start_index + rx)
            row_map_data = dict()
            for map_key in self.source_table_map.keys():
                if self.source_table_map.get(map_key) == -1:
                    continue
                _col_val = _row_data[self.source_table_map.get(map_key)]
                row_map_data[map_key] = _col_val.value if _col_val is not None else None

                _map_key_idx = self.source_table_map.get(map_key)
                # 识别一普表格年代信息
                if map_key == '年代':
                    if _row_data[_map_key_idx + 3] is not None and len(_row_data[_map_key_idx + 3].value) > 0:
                        row_map_data[map_key] = _row_data[_map_key_idx + 3].value
                    elif _row_data[_map_key_idx + 2] is not None and len(_row_data[_map_key_idx + 2].value) > 0:
                        row_map_data[map_key] = _row_data[_map_key_idx + 2].value
                    elif _row_data[_map_key_idx + 1] is not None and len(_row_data[_map_key_idx + 1].value) > 0:
                        row_map_data[map_key] = _row_data[_map_key_idx + 1].value
                    elif _row_data[_map_key_idx] is not None and len(_row_data[_map_key_idx].value) > 0:
                        row_map_data[map_key] = _row_data[_map_key_idx].value
                # 识别一普表格编号
                if map_key == '编号类型':
                    _code_map_key_idx = self.source_table_map.get('编号')
                    _code_type = _row_data[_map_key_idx].value
                    _code = _row_data[_code_map_key_idx].value
                    if util.str_index(_code_type, '总登记号') >= 0 or _code_type is None or len(_code_type) == 0:
                        row_map_data['总登记号'] = _code
                    else:
                        row_map_data['其他编号类型'] = _code_type
                        row_map_data['其他编号'] = _code



            # logger.info("%s 读取数据：%s", xls_file['desc'],
            #             '  '.join(list(map(lambda v: "{}:{}".format(v, row_map_data.get(v)), row_map_data.keys()))))

            if rx % self.export_xls_max_count == 0:
                if 'path' in cur_coll_xls.keys():
                    cur_coll_xls['book'].save(cur_coll_xls['path'])
                cur_coll_xls['path'] = os.path.join(self.export_xls_path, '藏品导入{}_{}_{}{}.xlsx'.format(
                    '_{}'.format(len(export_xls_list) + 1) if self.export_xls_max_count < xls_data_count else '',
                    xls_file['name'], xls_data_count,
                    '_start_{}'.format(rx) if self.export_xls_max_count < xls_data_count else ''))
                export_xls_list.append(cur_coll_xls['path'])
                shutil.copy(IMPORT_COLLECTION_XLS_TPL_FILE, cur_coll_xls['path'])
                cur_coll_xls['book'] = openpyxl.load_workbook(cur_coll_xls['path'])
                cur_coll_xls['sheet'] = cur_coll_xls['book'].worksheets[0]
                logger.info("%s输出表格：%s", xls_file['desc'], cur_coll_xls['path'])
            if rx % self.export_xls_max_count < self.export_xls_max_count:
                cur_coll_row_data = []
                for _key in IMPORT_COLLECTION_XLS_TITLE_ARRAY:
                    _value = None
                    if _key in row_map_data.keys():
                        _value = row_map_data[_key]
                        # 去除非法字符
                        _value = ILLEGAL_CHARACTERS_RE.sub(r'', _value) if type(_value) == str else _value
                    cur_coll_row_data.append(_value)

                cur_coll_xls['sheet'].append(cur_coll_row_data)
                if rx == (xls_sheet.nrows - self.source_xls_data_start_index - 1):
                    cur_coll_xls['book'].save(cur_coll_xls['path'])

        return list(map(lambda v: util.file_info(v), export_xls_list))
        pass

    def direct_start(self):
        logger.info("配置信息：%s", self.config_desc())

        total_xls_count = len(self.xls_list)
        export_table_count = 0
        task_start_time = datetime.datetime.now()
        fail_xls_name_list = []  # 转换失败的表格

        for i, _one_file in enumerate(self.xls_list):
            desc = '序号.{0}/{1}【{2}】'.format(str(i + 1), total_xls_count, _one_file['origin_name'])
            start_time = datetime.datetime.now()
            logger.info("%s 转换中..", desc)
            _one_file['desc'] = desc
            coverted_xls_files = self.convert_batch_coll_import_xls(_one_file)

            end_time = datetime.datetime.now()
            elapsed_sec = (end_time - start_time).seconds
            desc += "转换耗时：{} 秒".format(elapsed_sec)

            if coverted_xls_files is None:
                logger.error("%s转换表格遇到错误。表格路径：%s", desc, _one_file['full_path'])
                fail_xls_name_list.append(_one_file['origin_name'])
                shutil.copy(_one_file.get('full_path'),
                            os.path.join(self.export_xls_path, _one_file.get('origin_name')))
                continue
            export_table_count += len(coverted_xls_files)

            logger.info("%s，输出了 %s 个表格，分别是：%s。", desc, len(coverted_xls_files),
                        '、'.join(list(map(lambda v: v['origin_name'], coverted_xls_files))))
        task_end_time = datetime.datetime.now()
        task_elapsed_sec = (task_end_time - task_start_time).seconds

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
    export_xls_max_count = sys.argv[2]
    xls_path = sys.argv[3]
    CollXlsConvert(xls_path, export_xls_path=None, export_xls_max_count=int(export_xls_max_count), source_xls_data_start_index=int(source_xls_data_start_index)).direct_start()
    # CollXlsConvert('/Users/potato/Desktop/n5', export_xls_max_count=1000, export_xls_path=None,
    #                source_xls_data_start_index=3).direct_start()
