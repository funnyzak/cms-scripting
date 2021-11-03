#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
   created     ： The Jun 08 11:53 AM 2021
   filename    ： scan_folder_and_copy_to.py
   author      :  Leon
   email       :  silenceace@gmail.com
   Description : 复制文件夹列表指定文件（并对资源文件进行顺序重命名）并输出到指定输出文件夹
"""
__author__ = 'Leon'

import os
from config import (global_config)
import shutil
from common import (new_logger, PException)
from common.util import (
    sub_dirs,
    now_ts_s,
    is_match,
    search_files,
    send_wechat,
    ts_2_d,
    second_2_td
)

LOGGER_FILE_NAME = 'scan_folder_res_and_copy_to{}.log'.format(str(now_ts_s()))
logger = new_logger(LOGGER_FILE_NAME)


class ScanFolderAndCopyTo:
    """
    复制文件夹列表指定文件并输出到指定输出文件夹
    """

    def __init__(self):
        self._start_ts = now_ts_s()
        self._folder_path = global_config.get_raw('scan_folder_res_copy_to', 'folder_path')
        self._output_path = global_config.get_raw('scan_folder_res_copy_to', 'output_path')
        self._folder_match_pattern = global_config.get_raw('scan_folder_res_copy_to', 'folder_match_pattern')
        self._search_ext_list = global_config.get_raw('scan_folder_res_copy_to', 'search_ext_list')
        _sub_dir_list_rlt = self.get_subdir_from_root(self._folder_path)
        self._sub_dir_list_rlt = [] if _sub_dir_list_rlt is None else _sub_dir_list_rlt['list']
        self._sub_dir_list_no_match = [] if _sub_dir_list_rlt is None else _sub_dir_list_rlt['no_match']
        self._message = global_config.config['messenger'].getboolean('enable')
        self._jsd_key = global_config.get_raw('messenger', 'jsdkey')

    def config_desc(self):
        """
        打印配置
        """
        con_desc = "要处理的根目录文件夹：{}\n".format(self._folder_path)
        con_desc += "复制资源输出的文件夹：{}\n".format(self._output_path)
        con_desc += "匹配文件夹正则规则：{}\n".format(self._folder_match_pattern)
        con_desc += "要搜索的资源文件格式：{}\n".format(self._search_ext_list)
        return con_desc
        pass

    def start_check(self):
        if not os.path.exists(self._folder_path):
            raise PException("扫描资源目录不存在，请检查")
        if len(self._sub_dir_list_rlt) == 0:
            raise PException("未找到匹配的待处理文件夹。")

        if not os.path.exists(self._output_path):
            os.makedirs(self._output_path)

        logger.info("配置信息：%s", self.config_desc())

        logger.info("文件夹过滤后，找到符合 %s 名称规则的文件夹有 %s 个，分别是：\n%s。 \n\n不符合的文件夹有 %s 个，分别是：\n%s。\n\n",
                    self._folder_match_pattern, len(self._sub_dir_list_rlt),
                    '\n'.join(list(map(lambda v: '文件夹：{} '.format(v['dir_name']), self._sub_dir_list_rlt))),
                    len(self._sub_dir_list_no_match),
                    '无' if len(self._sub_dir_list_no_match) == 0 else '\n'.join(
                        list(map(lambda v: v['dir_name'], self._sub_dir_list_no_match)))
                    )
        pass

    def get_subdir_from_root(self, root_path):
        """
        从根目录获取匹配的文件夹
        :param root_path:
        :return:
        """
        match_list = []
        no_match_list = []

        dir_list = sub_dirs(root_path)
        if dir_list is None:
            return None

        for dir_one in dir_list:
            if not is_match(dir_one['dir_name'], self._folder_match_pattern):
                no_match_list.append(dir_one)
                continue
            match_list.append(dir_one)
        return dict(list=match_list, no_match=no_match_list)
        pass

    def scan_folder(self):
        """
        开始扫描文件夹并资源入库
        """
        self.start_check()

        total_dir_count = len(self._sub_dir_list_rlt)
        total_res_count = 0
        success_res_count = 0

        for idx, dir_one in enumerate(self._sub_dir_list_rlt):
            one_desc = "序号.{1}【{0}】 ===> ".format(dir_one.get('dir_name'), idx + 1)
            dir_one['index'] = idx + 1
            dir_one['info'] = one_desc
            logger.info("%s原始路径 %s。", one_desc, dir_one.get('dir_path'))

            dir_one['res_list'] = search_files(dir_one['dir_path'], self._search_ext_list.split(','))
            dir_one['res_count'] = len(dir_one['res_list'])  # 资源总数
            if dir_one['res_count'] == 0:
                logger.info("%s未找到可处理资源,已跳过。", one_desc)
                continue
            total_res_count += dir_one['res_count']

            for idx, res in enumerate(dir_one['res_list']):
                target_path = os.path.join(self._output_path,
                                           dir_one['dir_name'] + '_' + str(idx + 1)) + '.' + res['ext']
                try:
                    shutil.copy(res['full_path'], target_path)
                    logger.info("%s已复制文件：%s 到目标文件 %s", dir_one['info'], res['full_path'], target_path)
                    success_res_count += 1
                    idx += 1
                except Exception as e:
                    logger.error("%s复制文件发生意外错误。source:%s, target:%s。错误信息：%s", dir_one['info'], res['full_path'],
                                 target_path, e)

        end_ts = now_ts_s()
        elapsed_td = second_2_td(end_ts - self._start_ts)
        summary = "扫描文件夹 {}，处理了 {} 个文件夹。共找到资源数：{} 个, 成功处理资源数: {} 个。任务开始于：{}，总耗时：{}。".format(
            self._folder_path,
            total_dir_count,
            total_res_count,
            success_res_count,
            ts_2_d(self._start_ts),
            elapsed_td
        )

        logger.info(summary)

        if self._message:
            send_wechat(self._jsd_key, "复制文件夹列表指定文件格式并输出到指定输出文件夹完成。", summary)

if __name__ == '__main__':
    ScanFolderAndCopyTo().scan_folder()

