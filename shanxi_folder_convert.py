#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
   created     ： The Sep 30 17:58 PM 2021
   filename    ： shanxi_folder_convert.py
   author      :  Leon
   email       :  silenceace@gmail.com
   Description :  昆仑文保博物馆数据移交硬盘转换为山西博物院数据盘文件夹文件格式（三维）
"""
__author__ = 'Leon'

import os
import shutil

from config import (global_config)
from common import *
from common.util import (
    sub_dirs,
    now_ts_s,
    make_dirs,
    remove_file,
    is_match,
    send_wechat,
    ts_2_d,
    second_2_td,
    match_group
)

LOGGER_FILE_NAME = 'kl_shanxi_data_convert.log'
logger = new_logger(LOGGER_FILE_NAME)


class ShanxiFolderConvert:
    def __init__(self, source_folder_path=None, output_folder_path=None):
        """
        :param source_folder_path: 要处理的源数据盘文件夹
        :param output_folder_path: 转换输出的硬盘
        """

        self._target_path = output_folder_path
        self._root_path = source_folder_path

        self._start_ts = now_ts_s()

        # 获取子文件夹匹配规则
        self._match_dir_pattern = global_config.get_raw('scan_res', 'match_dir_pattern')

        self._message = global_config.config['messenger'].getboolean('enable')
        self._jsd_key = global_config.get_raw('messenger', 'jsdkey')
        _sub_dir_list_rlt = self.get_subdir_from_root(self._root_path)
        self.sub_dir_list = [] if _sub_dir_list_rlt is None else _sub_dir_list_rlt['list']
        self.sub_dir_list_no_match = [] if _sub_dir_list_rlt is None else _sub_dir_list_rlt['no_match']

        pass

    @classmethod
    def show_option_start(cls):
        print("昆仑文保博物馆数据移交硬盘转换为山西博物院数据盘文件夹文件格式。")
        source_path = input("请输入昆仑数据移交盘的根目录文件夹路径：")
        output_path = input("请输入山西博物院数据盘文件夹输出路径：")
        cls(source_path, output_path).direct_start()

    def start_check(self):
        if self._root_path is None or len(self._root_path) == 0:
            raise PException('请设置要处理的根目录文件夹')
        if not os.path.exists(self._root_path):
            raise PException('要处理的文件夹不存在')
        dir_list = util.sub_dirs(self._root_path)
        if len(dir_list) == 0:
            raise PException('要处理的文件夹不存在下级文件夹')
        if not os.path.exists(self._target_path):
            os.makedirs(self._target_path)

        logger.info("配置信息：%s", self.config_desc())

        logger.info("文件夹过滤后，找到符合 %s 名称规则的文件夹有 %s 个，分别是：\n%s。 \n\n不符合的文件夹有 %s 个，分别是：\n%s。\n\n",
                    self._match_dir_pattern, len(self.sub_dir_list),
                    '\n'.join(list(map(lambda v: '文件夹：{} 编号：{} 名称：{}'.format(v['dir_name'],
                                                                             v['num'], v['name']), self.sub_dir_list))),
                    len(self.sub_dir_list_no_match),
                    '无' if len(self.sub_dir_list_no_match) == 0 else '\n'.join(
                        list(map(lambda v: v['dir_name'], self.sub_dir_list_no_match)))
                    )
        pass

    def config_desc(self):
        """
        打印配置
        """
        con_desc = "扫描资源目录：{}\n".format(self._root_path)
        con_desc += "输出文件夹为：{}\n".format(self._target_path)
        con_desc += "获取匹配操作文件夹的正则表达式：{}\n".format(self._match_dir_pattern)
        return con_desc
        pass

    def get_subdir_from_root(self, root_path):
        """
        从根目录获取匹配的文物文件夹
        :param root_path:
        :return:
        """
        match_list = []
        no_match_list = []

        dir_list = sub_dirs(root_path)
        if dir_list is None:
            return None

        for dir_one in dir_list:
            if not is_match(dir_one['dir_name'], self._match_dir_pattern):
                no_match_list.append(dir_one)
                continue
            mgs = match_group(dir_one['dir_name'], self._match_dir_pattern)
            dir_one['num'] = mgs.group('num')
            dir_one['name'] = mgs.group('name')
            match_list.append(dir_one)
            #######判断并加入藏品是否有子组件文件夹
            sub_dir_list = self.get_subdir_from_root(dir_one['dir_path'])
            if sub_dir_list is None:
                continue
            match_list.extend(sub_dir_list['list'])
        return dict(list=match_list, no_match=no_match_list)
        pass

    def folder_convert(self, dir_info):
        dir_target_dir_name = '{}_{}_3'.format(dir_info['num'], dir_info['name'])
        dir_target_path = os.path.join(self._target_path, dir_target_dir_name)

        # 压缩模型数据到目标文件夹
        dir_target_path_high = os.path.join(dir_target_path, 'high')
        dir_target_path_low = os.path.join(dir_target_path, 'low')
        dir_target_path_high_zip = os.path.join(dir_target_path_high,
                                                '{}_{}_高精度.zip'.format(dir_info['num'], dir_info['name']))
        dir_target_path_low_zip = os.path.join(dir_target_path_low,
                                               '{}_{}_低精度.zip'.format(dir_info['num'], dir_info['name']))

        if not os.path.exists(dir_target_path_low):
            os.makedirs(dir_target_path_low)

        if not os.path.exists(dir_target_path_high):
            os.makedirs(dir_target_path_high)

        _dir_3d_model_path = os.path.join(dir_info['dir_path'], '成果模型')

        if not os.path.exists(_dir_3d_model_path):
            return
        else:
            # 低精度模型处理
            remove_file(dir_target_path_low_zip)
            model_dir_arr = self.search_3d_model(_dir_3d_model_path, 'low')
            if model_dir_arr is not None:
                for _model_path in model_dir_arr:
                    logger.info("%s 正在对 %s 进行压缩，输出到：%s。", dir_info['info'], _model_path['dir_path'],
                                dir_target_path_low_zip)
                    try:
                        ZipUtil.add_files_to_zip(dir_target_path_low_zip, _model_path['dir_path'], False)
                    except Exception as err:
                        logger.error("%s 对 %s 进行压缩失败 %s", dir_info['info'], dir_target_path_low_zip, err)

            # 高精度模型处理

            remove_file(dir_target_path_high_zip)
            model_dir_arr = self.search_3d_model(_dir_3d_model_path, 'high')
            if model_dir_arr is not None:
                remove_file(os.path.join(dir_target_path_high, 'tmp', '高精度成果模型'))
                shutil.copytree(model_dir_arr[0]['dir_path'], os.path.join(dir_target_path_high, 'tmp', '高精度成果模型'),
                                dirs_exist_ok=True)

            model_dir_arr = self.search_3d_model(_dir_3d_model_path, 'mid')
            if model_dir_arr is not None:
                remove_file(os.path.join(dir_target_path_high, 'tmp', '中精度成果模型'))
                shutil.copytree(model_dir_arr[0]['dir_path'], os.path.join(dir_target_path_high, 'tmp', '中精度成果模型'),
                                dirs_exist_ok=True)

            for _model_path in model_dir_arr:
                logger.info("%s 正在对 %s 进行压缩，输出到：%s。", dir_info['info'], dir_target_path_high,
                            dir_target_path_high_zip)
                try:
                    ZipUtil.add_files_to_zip(dir_target_path_high_zip, os.path.join(dir_target_path_high, 'tmp'))
                    remove_file(os.path.join(dir_target_path_high, 'tmp'))
                except Exception as err:
                    logger.error("%s 对 %s 进行压缩失败 %s", dir_info['info'], dir_target_path_high, err)

        # 压缩原始数据到目标文件夹
        dir_target_path_origin = os.path.join(dir_target_path, 'original')
        dir_target_path_origin_zip = os.path.join(dir_target_path_origin,
                                                  '{}_{}_原始文件.zip'.format(dir_info['num'], dir_info['name']))

        if not os.path.exists(dir_target_path_origin):
            os.makedirs(dir_target_path_origin)
        for _dir_name in ['成果照片', '采集照片', '采集三维']:
            _origin_sub_path = os.path.join(dir_info['dir_path'], _dir_name)
            if os.path.exists(_origin_sub_path):
                logger.info("%s 正在对 %s 进行压缩，输出到：%s。", dir_info['info'], _origin_sub_path, dir_target_path_origin_zip)
                try:
                    ZipUtil.add_files_to_zip(dir_target_path_origin_zip, _origin_sub_path, True)
                except Exception as err:
                    logger.error("%s 对 %s 进行压缩失败 %s", dir_info['info'], dir_target_path_origin_zip, err)

        pass

    def search_3d_model(self, root_path, level='high'):
        if not os.path.exists(root_path):
            return None
        return list(
            filter(lambda x: is_match(x['dir_name'], level), sub_dirs(root_path)))
        pass

    def direct_start(self):
        self.start_check()
        total_dir_count = len(self.sub_dir_list)
        success = 0

        for idx, dir_one in enumerate(self.sub_dir_list):
            one_desc = "序号.{3}【{2}】，提取编号：{0}，提取名称：{1} ===> ".format(
                dir_one.get('num'), dir_one.get('name'), dir_one.get('dir_name'), idx + 1)
            dir_one['index'] = idx + 1
            dir_one['info'] = one_desc
            logger.info("%s原始路径 %s。", one_desc, dir_one.get('dir_path'))

            # 复制转换文件夹
            self.folder_convert(dir_one)
            dir_one['op'] = True
            success += 1

        end_ts = now_ts_s()
        elapsed_td = second_2_td(end_ts - self._start_ts)

        summary = "扫描文件夹 {}，处理了 {} 个文件夹，其中成功 {} 个，待确认 {} 个。任务开始于：{}，总耗时：{}。{}".format(
            self._root_path,
            total_dir_count,
            success,
            total_dir_count - success,
            ts_2_d(self._start_ts),
            elapsed_td,
            '' if success == total_dir_count else '\n其中待处理文件夹如下：\n{}'.format(
                '\n'.join(
                    list(map(
                        lambda v: v[
                            'dir_name'],
                        list(filter(
                            lambda
                                x: 'op' not in x.keys(),
                            self.sub_dir_list))

                    )))
            ))
        logger.info(summary)

        if self._message:
            send_wechat(self._jsd_key, "扫描磁盘转换山西博物院移交盘完成。", summary)

        pass


if __name__ == '__main__':
    ShanxiFolderConvert('/Volumes/MAF/Down/昆仑数据整理格式范例', '/Volumes/MAF/Down/山西博物馆移交盘格式输出2').direct_start()
