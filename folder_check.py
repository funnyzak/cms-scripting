#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
   created     ： The Feb 03 11:52 AM 2021
   filename    ： folder_check.py.py
   author      :  Leon
   email       :  silenceace@gmail.com
   Description :  根据配置检查各文物文件夹对应的下级文件夹文件整理情况
"""
__author__ = 'Leon'

import os
from functools import reduce

from common import *
from config import folder_check_config

LOGGER_FILE_NAME = 'folder_check.log'
logger = new_logger(LOGGER_FILE_NAME)


class FolderChecker:
    def __init__(self, check_folder_path=None):
        """
        :param check_folder_path: 要检查的目标文件夹
        """
        if check_folder_path is None or len(check_folder_path) == 0:
            raise PException('请设置要检查的目标文件夹')
        if not os.path.exists(check_folder_path):
            raise PException('目标文件夹不存在')
        dir_list = util.sub_dirs(check_folder_path)
        if len(dir_list) == 0:
            raise PException('该目标目录不存在下级文件夹')

        self.check_config = folder_check_config
        self.dir_list = dir_list
        pass

    @classmethod
    def config_desc(cls, check_config):
        return '\n'.join(
            list(
                map(
                    lambda v: "从业务文件夹的【{}】目录下，搜索所有的：【{}】格式。".format(
                        v['dir_name'].replace('/', os.path.sep),
                        '、'.join(
                            [] if v['ext_list'] is None else
                            v['ext_list'])),
                    check_config)
            )
        )

    def check_dir(self, sub_dir):
        check_info_list = []
        for dir_config in self.check_config:
            check_info = dict()
            check_info['config'] = dir_config
            config_dir_name = dir_config['dir_name'].replace('/', os.path.sep)
            config_ext_list = dir_config['ext_list']
            cur_check_path = os.path.join(sub_dir['dir_path'], config_dir_name)
            if not os.path.exists(cur_check_path):
                check_info['err'] = '不存在文件夹 {}。'.format(cur_check_path)
                check_info_list.append(check_info)
                continue

            search_files = util.search_files(cur_check_path, config_ext_list)
            if len(search_files) == 0:
                check_info['err'] = '{} 中不存在 {} 类型文件。'.format(cur_check_path, config_ext_list)
                check_info_list.append(check_info)
                continue
            check_info['res_count'] = len(search_files)
            check_info['res_size'] = reduce(lambda x, y: x + y, list(map(lambda x: x['size'], search_files)))
            check_info['res_desc'] = '{} 中包含 {} 类型文件 {} 个，总大小 {}。'.format(cur_check_path, config_ext_list,
                                                                          len(search_files),
                                                                          util.human_size(check_info['res_size']))
            check_info_list.append(check_info)
        fail_check_list = list(filter(lambda x: 'err' in x.keys(), check_info_list))
        success_check_list = list(filter(lambda x: 'err' not in x.keys(), check_info_list))
        return dict(check_list=check_info_list,
                    success_list=success_check_list,
                    fail_list=fail_check_list,
                    fail_dir_list=list(
                        map(lambda x: x['config']['dir_name'].replace('/', os.path.sep), fail_check_list)),
                    res_info='\n'.join(list(map(lambda x: x['res_desc'], success_check_list))),
                    errors_info='\n'.join(list(map(lambda x: x['err'], fail_check_list))),
                    all_ok=len(check_info_list) == len(success_check_list))
        pass

    @classmethod
    def show_option_start(cls):
        print("根据配置检查各文物文件夹对应的下级文件夹文件整理情况。" \
              "目前的检查规则为：\n{}\n(如需修改检查配置，请修改 config.json=>folder_check_config项)\n".format(FolderChecker.config_desc(folder_check_config)))
        check_path = input("请输入待检查的文件夹路径：")
        cls(check_path).direct_start()

    def direct_start(self):
        logger.info("扫描共有 %s 个下级文件夹。现在开始扫描检查..\n\n", len(self.dir_list))

        ok_list = []
        no_list = []
        for idx, dir_info in enumerate(self.dir_list):
            dir_desc = '序号.{}，扫描 {} 中'.format(idx + 1, dir_info['dir_path'])
            logger.info(dir_desc + '..')
            check_rlt = self.check_dir(dir_info)
            dir_info['check_info'] = check_rlt
            if check_rlt['all_ok']:
                ok_list.append(dir_info)
                logger.info('%s，该文件夹【合格】，资源文件夹汇总：\n%s\n\n\n\n\n', dir_desc, check_rlt['res_info'])
            else:
                no_list.append(dir_info)
                logger.info('%s，该文件夹【待检查】，其中资源文件夹汇总：\n%s\n', dir_desc, check_rlt['res_info'])
                logger.error('%s，待检查资源文件夹汇总如下：\n%s\n\n\n\n\n', dir_desc, check_rlt['errors_info'])

        _log_info = '共扫描检查 {} 个文件夹，完整文件夹 {} 个，待检查文件夹 {} 个。\n\n' \
                    '待检查的文件夹分别是：\n{}，\n\n详细和历史记录请看日志 {}。'.format(len(self.dir_list),
                                                                 len(ok_list), len(no_list),
                                                                 '\n'.join(
                                                                     list(map(
                                                                         lambda x: '{} 中文件夹=> {}'.format(x['dir_path'],
                                                                                                         '、'.join(x[
                                                                                                                      'check_info'][
                                                                                                                      'fail_dir_list'])),
                                                                         no_list))),
                                                                 LOGGER_FILE_NAME)
        logger.info(_log_info)


if __name__ == '__main__':
    FolderChecker.show_option_start()
