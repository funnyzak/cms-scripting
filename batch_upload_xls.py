#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
   created     ： The Aug 06 4:29 PM 2021
   filename    ： batch_upload_xls.py.py
   author      :  Leon
   email       :  silenceace@gmail.com
   Description : 批量导入Execl表格到藏品系统
   使用：python3 batch_upload_xls.py '1' '/Users/potato/Desktop/test3'
   参数1：1/2 导入藏品信息/导入柜架信息  参数2：要导入的表格路径
"""
__author__ = 'Leon'

import os, sys
from common import *
from api_coll import ApiColl
import datetime
import requests
import shutil
from common.util import (
    send_wechat
)
from config import (global_config)

LOGGER_FILE_NAME = 'upload_execl.log'
logger = new_logger(LOGGER_FILE_NAME)


class BatchUploadXls:
    def __init__(self, source_xls_path=None, import_type=None):
        """
        :param source_xls_path: 要批量导入的表格源路径
        """
        if source_xls_path is None or len(source_xls_path) == 0:
            raise PException('请正确设置Execl表格文件夹路径')
        if not os.path.exists(source_xls_path):
            raise PException('Execl表格文件夹路径不存在')
        self.xls_list = util.search_files(root=source_xls_path, ext_list=['xls', 'xlsx'], deep_search=False)
        if len(self.xls_list) == 0:
            raise PException('该目录不存在导入的表格')
        if import_type is None or import_type not in [1, 2]:
            import_type = 1

        self.coll_api = ApiColl()
        self.session = self.coll_api.session_user
        self.mid = self.session['user']['mid']
        self.uid = self.session['user']['id']
        self._message = global_config.config['messenger'].getboolean('enable')
        self._jsd_key = global_config.get_raw('messenger', 'jsdkey')
        self.source_xls_path = source_xls_path
        self.export_xls_path = os.path.join(self.source_xls_path, util.now_d_str("task%H%M%S"))
        self.import_type = import_type
        for xls_file in self.xls_list: shutil.copy2(xls_file['full_path'], self.backup_path('源备份')) # 备份要处理的表格
        pass

    def config_desc(self):
        con_desc = "\n处理的表格文件夹：{}\n".format(self.source_xls_path)
        con_desc += "导入类型（1=>导入藏品 2=>导入柜架）：{}\n".format(self.import_type)
        con_desc += "要导入的表格分别为：\n{}\n\n".format(
            '\n'.join(
                list(
                    map(lambda v: v['origin_name'], self.xls_list)
                )
            )
        )
        con_desc += "要导入的表格数：{}\n".format(len(self.xls_list))
        return con_desc
        pass

    @classmethod
    def show_option_start(cls):
        import_file_path = input("请输入要导入的源表格文件夹路径：")
        import_type = input("请输入导入类型（1=>导入藏品 2=>导入柜架）：")
        cls(import_file_path, int(import_type)).direct_start()

    def backup_path(self, identify = 'success'):
        target_path = os.path.join(self.export_xls_path, identify)
        if not os.path.exists(target_path):
            os.makedirs(target_path)
        return target_path

    def backup_file_path(self, source_file, identify = 'success', save_name = None):
        return os.path.join(self.backup_path(identify), '{}.{}'.format(save_name if save_name is not None else source_file.get('name'), source_file.get('ext')))

    def backup_cp_file(self, source_file, identify = 'success', save_name = None):
        save_path = self.backup_file_path(source_file, identify, save_name)
        if os.path.exists(save_path):
            os.remove(save_path)
        shutil.copy2(source_file.get('full_path'), save_path)

    def backup_mv_file(self, source_file, identify = 'success', save_name = None):
        save_path = self.backup_file_path(source_file, identify, save_name)
        if os.path.exists(save_path):
            os.remove(save_path)
        shutil.move(source_file.get('full_path'),  save_path)

    def direct_start(self):
        logger.info("配置信息：%s", self.config_desc())

        total_xls_count = len(self.xls_list)
        total_data_count = 0  # 共处理数据数
        success_data_count = 0  # 成功导入数据熟练
        fail_xls_name_list = [] # 导入失败的表格
        has_err_data_name_list = [] # 有错误行的表格

        task_start_time = datetime.datetime.now()
        for i, _one_file in enumerate(self.xls_list):
            desc = '序号.{0}/{1}【{2}】'.format(str(i + 1), total_xls_count, _one_file['origin_name'])

            rlt = None
            logger.info("%s 导入中...", desc)

            start_time = datetime.datetime.now()
            if self.import_type == 1:
                rlt = self.coll_api.coll_table_upload(self.mid, _one_file.get('full_path'))
            elif self.import_type == 2:
                rlt = self.coll_api.coll_storage_table_upload(self.mid, _one_file.get('full_path'))
            end_time = datetime.datetime.now()
            api_elapsed_sec = (end_time - start_time).seconds

            desc += "导入耗时：{} 秒. ".format(api_elapsed_sec)
            if rlt is None:
                logger.error("%s上传表格遇到错误。 表格路径：%s", desc, _one_file['full_path'])
                fail_xls_name_list.append(_one_file['origin_name'])
                self.backup_cp_file(_one_file, '导入失败')
                continue
            else:
                pass

            total_data_count += rlt['total']
            success_data_count += rlt['success']
            logger.info("%s 此表格处理耗时 %s 秒，找到 %s 个记录，成功 %s 个，失败 %s 个。", desc, api_elapsed_sec, rlt['total'],
                        rlt['success'], rlt['fail'])

            self.backup_mv_file(_one_file, '成功导入')
            # 错误表格信息保存到本地
            if rlt['fail'] > 0:
                has_err_data_name_list.append(_one_file['origin_name'])
                xls_down_url = rlt['failRecordFile']['url']
                r = requests.get(xls_down_url if xls_down_url.index('/') > 0 else self.coll_api._api_base_url + xls_down_url)
                with open(self.backup_file_path(_one_file, '错误记录'), "wb") as code:
                    code.write(r.content)

        task_end_time = datetime.datetime.now()
        task_elapsed_sec = (task_end_time - task_start_time).seconds

        summary = "处理表格文件夹: {}, 共处理 {} 个表格, 导入成功 {} 个表格，导入失败表格 {} 个。\n任务开始于：{}，总耗时：{} 秒。 共处理 {} 个记录，成功 {} 个, 失败 {} 个。\n表格有失败行是：{}。 \n处理失败的表格是：{}。".format(
            self.source_xls_path,
            len(self.xls_list),
            len(self.xls_list) - len(fail_xls_name_list),
            len(fail_xls_name_list),
            task_start_time,
            task_elapsed_sec,
            total_data_count,
            success_data_count,
            total_data_count - success_data_count,
            '无' if len(
                has_err_data_name_list) == 0 else
            '、'.join(
                has_err_data_name_list),
            '无' if len(
                fail_xls_name_list) == 0 else
            '、'.join(
                fail_xls_name_list))
        logger.info('\n\n' + summary)
        if self._message:
            send_wechat(self._jsd_key, "表格导入完成。", summary)


if __name__ == '__main__':
    import_type = sys.argv[1]
    xls_path = sys.argv[2]
    BatchUploadXls(xls_path, import_type=int(import_type)).direct_start()
