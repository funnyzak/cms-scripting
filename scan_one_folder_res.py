#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
   created     ： The Jun 05 3:24 PM 2021
   filename    ： scan_one_folder_res.py
   author      :  Leon
   email       :  silenceace@gmail.com
   Description :  扫描同一个文件夹的所有匹配的资源文件，并根据规则入库到对应的资源库
"""
__author__ = 'Leon'

import os
import json
from database import DataBase
from config import (global_config,
                    get_res_num_rules,
                    coll_info_num_field_set,
                    resource_cate_ext_config)
from functools import reduce
import shutil
from api_coll import ApiColl
from common import (FileUtil, ZipUtil, new_logger, PException)
from common.util import (
    sub_dirs,
    now_ts_s,
    is_match,
    human_size,
    search_files,
    send_wechat,
    file_hash,
    ts_2_d,
    file_info,
    second_2_td,
    match_group,
    distinctList
)
from common.imgutil import (
    img_exif,
    is_img,
    is_photo,
    img_compress,
    img_size
)

LOGGER_FILE_NAME = 'scan_one_folder_res_{}.log'.format(str(now_ts_s()))
logger = new_logger(LOGGER_FILE_NAME)


class ScanOneFolderRes:
    """
    扫描同一个文件夹的所有匹配的资源文件，并入库到对应的资源库
    """

    def __init__(self):
        self.coll_api = ApiColl()
        self.session = self.coll_api.session_user
        self.mid = self.session['user']['mid']
        self.uid = self.session['user']['id']
        self.db = DataBase(self.uid, self.mid)
        self.db.re_connect()
        self.get_res_num_rules = get_res_num_rules
        self._start_ts = now_ts_s()
        self._museum_all_coll_info = self.db.coll_all()
        self._resource_url_prefix = global_config.get_raw('scan_res_common', 'resource_url_prefix')
        self._resource_storage_way = global_config.get_raw('scan_res_common', 'resource_storage_way')
        self._folder_path = global_config.get_raw('scan_one_folder_res', 'folder_path')
        self._cache_path = os.path.join(global_config.get_raw('scan_one_folder_res', 'cache_path'), str(now_ts_s()))
        self._scan_to_res_cate = global_config.get_raw('scan_one_folder_res', 'scan_to_res_cate')
        self._folder_all_res = search_files(self._folder_path,
                                            resource_cate_ext_config[self._scan_to_res_cate]['extList'], [])

        self._copy_target_path = global_config.get_raw('scan_res_common', 'copy_target_path')
        self._copy_target_path_rename = global_config.config['scan_res_common'].getboolean('copy_target_path_rename')
        self._check_rule_cate_same_res_count_ignore = global_config.config['scan_res'].getboolean(
            'check_rule_cate_same_res_count_ignore')
        self._copy_target_path_to_compress = global_config.config['scan_res_common'].getboolean(
            'copy_target_path_to_compress')
        self._copy_target_path_to_compress_quality = global_config.config['scan_res_common'].getint(
            'copy_target_path_to_compress_quality')
        self._copy_target_path_to_compress_scale_precent = global_config.config['scan_res_common'].getint(
            'copy_target_path_to_compress_scale_precent')
        self._message = global_config.config['messenger'].getboolean('enable')
        self._jsd_key = global_config.get_raw('messenger', 'jsdkey')
        if not os.path.exists(self._cache_path):
            os.makedirs(self._cache_path)

    def config_desc(self):
        """
        打印配置
        """
        con_desc = "\nDB Host：{}\n".format(global_config.get_raw('db', 'mysql_host'))
        con_desc += "DB Port：{}\n".format(global_config.get_raw('db', 'mysql_port'))
        con_desc += "DB Database：{}\n".format(global_config.get_raw('db', 'mysql_database'))
        con_desc += "DB User：{}\n".format(global_config.get_raw('db', 'mysql_user'))
        con_desc += "DB Password：{}\n".format(global_config.get_raw('db', 'mysql_password'))
        con_desc += "API Base URL：{}\n".format(global_config.get_raw('coll', 'api_base_url'))
        con_desc += "系统登陆用户信息：{}\n".format(json.dumps(self.session['user'], ensure_ascii=False))
        con_desc += "要操作的文件夹路径：{}\n".format(self._folder_path)
        con_desc += "缓存文件夹：{}\n".format(self._cache_path)
        con_desc += "要扫描资源入库对应的资源类型：{}\n".format(self._scan_to_res_cate)
        return con_desc
        pass

    def start_check(self):
        if not os.path.exists(self._folder_path):
            raise PException("要处理的目录 {} 不存在，请检查".format(self._folder_path))
        if self.session['user']['mid'] is None:
            raise PException('请登陆博物馆管理账户')
        if self._folder_all_res is None or len(self._folder_all_res) == 0:
            raise PException('要处理的目录没有对应资源文件')
        if self._museum_all_coll_info is None or len(self._museum_all_coll_info) == 0:
            raise PException('该博物馆没有任何藏品信息')

        logger.info("配置信息：%s", self.config_desc())

        pass

    def cache_file(self, source_path):
        """
        失败文件缓存
        :param source_path:
        :return:
        """
        shutil.copy(source_path, os.path.join(self._cache_path, os.path.split(source_path)[1]))

    def analysis_file_num(self, one_file):
        """
        分析文件，并匹配规则
        :param one_file:
        :return:
        """
        for i, _rule in enumerate(get_res_num_rules):
            mgs = match_group(one_file['name'], _rule['expression'])
            if mgs is None:
                continue

            one_file['match'] = dict(num=mgs.group('num'), name=mgs.group('name'),
                                     rule=_rule,
                                     dbdata=self.search_db_coll_info_by_num(coll_info_num_field_set[_rule['field']],
                                                                            mgs.group('num'), _rule['otherType']))
            break
        return one_file
        pass

    def search_db_coll_info_by_num(self, num_field, num_field_value, other_type):
        for _item_info in self._museum_all_coll_info:
            if _item_info[num_field] == num_field_value:
                if len(num_field.split('_other')) == 1:
                    return _item_info
                elif _item_info['c_other_type'] == other_type:
                    return _item_info

        return None
        pass

    def copy_res_to_target_dir(self, res, desc):
        if self._copy_target_path == '':
            return None
        source_path = res['full_path']
        target_path = os.path.join(self._copy_target_path, res['full_path'].replace(self._folder_path, "")[1:])
        target_dir = target_path[0:len(target_path) - len(res['origin_name'])]
        if self._copy_target_path_rename:
            _file_date = ts_2_d(res['create_time'])
            target_dir = os.path.join(self._copy_target_path, str(self.mid), str(_file_date.year),
                                      str(_file_date.month) + str(_file_date.day))
            target_path = os.path.join(target_dir, res['md5'] + '.' + res['ext'])

        if not os.path.exists(target_path):
            if not os.path.exists(target_dir):
                os.makedirs(target_dir)
            try:
                compress_success = False
                if self._copy_target_path_to_compress and is_img(source_path):
                    compress_success = img_compress(source_path, target_path,
                                                    self._copy_target_path_to_compress_scale_precent,
                                                    self._copy_target_path_to_compress_quality)
                    if not compress_success:
                        shutil.copy(source_path, target_path)
                else:
                    shutil.copy(source_path, target_path)

                logger.info("%s已复制%s文件：%s 到目标文件 %s", desc, '' if not compress_success else '并压缩',
                            source_path, target_path)
            except Exception as e:
                logger.error("%s复制文件发生意外错误。source:%s, target:%s。错误信息：%s", desc, source_path, target_dir, e)
                return None
        return dict(target_dir=target_dir, target_path=target_path)
        pass

    def resource_exist_db_check(self, desc, md5s):
        if self.db.resource_one_by_md5(md5s):
            logger.info("%s已入库，不需要重新入库。", desc)
            return True
        return False

    def resource_add_by_db(self, desc, res):
        """
        通过DB的方式，资源直接入库
        """

        save_path = res['full_path'].replace(self._folder_path, "").replace(os.path.sep, "/")
        url = "{}{}".format(self._resource_url_prefix, save_path)

        logger.info("%s源路径：%s。", desc, res.get('full_path'))

        res_md5 = res['md5']
        res_size = res['size']
        _target_file = None
        if self._copy_target_path != '':
            _target_file = self.copy_res_to_target_dir(res, desc)
            res['target'] = file_info(_target_file['target_path'])
            save_path = _target_file['target_path'].replace(self._copy_target_path, '').replace(os.path.sep, "/")
            url = "{}{}".format(self._resource_url_prefix, save_path)
            res_md5 = file_hash(_target_file['target_path'])
            res_size = res['target']['size']

        if self.resource_exist_db_check(desc, res_md5):
            # if _target_file is not None and os.path.exists(_target_file['target_path']):
            #     os.remove(_target_file['target_path'])
            # 以上暂时去除，可能为误删已上传文件
            return

        exif_info = None if not is_photo(save_path) else img_exif(res['full_path'])  # 原图Exif信息
        ext_str = None if exif_info is None else json.dumps(dict(exif=exif_info))

        img_s = img_size(
            res.get('target').get('full_path') if 'target' in res.keys() else res['full_path'])  # 如果复制资源则使用新资源图片否则旧图
        ins_res = {
            'cate': self._scan_to_res_cate,
            'name': res.get('name'),
            'relationId': res['match']['dbdata']['id'],
            'belongType': 'COLLECTION_LOGIN_INFO',
            'description': None,
            'key': url,
            'ext': ext_str,
            'size': res_size,
            'contentType': res.get('mime'),
            'suffix': res.get('ext'),
            'cover': '' if not is_img(url) else url,
            'source': '',
            'width': 0 if img_s is None else img_s.get('width'),
            'height': 0 if img_s is None else img_s.get('height'),
            'ip': '127.0.0.1',
            'partCount': 1,
            'savePath': save_path,
            'md5': res_md5
        }
        self.db.add_resource(ins_res)
        logger.info("%s入库信息：%s。", desc, json.dumps(ins_res)[0:70] + '...')

    def resource_add_by_api(self, desc, res):
        """
        通过API的方式上传资源
        """
        logger.info("%s源路径：%s。", desc, res.get('full_path'))
        if self.resource_exist_db_check(desc, res['md5']):
            return
        rlt = self.coll_api.resource_upload(res['match']['dbdata']['id'], self._scan_to_res_cate, res['full_path'])
        if rlt is None:
            logger.error("%s上传资源遇到错误。 资源路径：%s", desc, res['full_path'])
            return
        logger.info("%s 已入库。 入库信息：%s。", desc, json.dumps(rlt)[0:70] + '...')

    def scan_folder(self):
        """
        开始扫描文件并入库数据库
        """
        self.start_check()

        folder_total_file_count = len(self._folder_all_res)

        match_list = []
        no_match_list = []
        match_not_db_list = []
        match_db_list = []
        res_total_size = 0

        for i, _one_file in enumerate(self._folder_all_res):
            _file_analysis_info = self.analysis_file_num(_one_file)
            res_total_size += _one_file['size']

            desc = '序号.{0}/{1}【{2}】'.format(str(i + 1), folder_total_file_count, _one_file['origin_name'])
            if 'match' not in _file_analysis_info.keys():
                no_match_list.append(_file_analysis_info)
                desc += '{0}==>不符合匹配规则，忽略此文件。'.format(desc)
                self.cache_file(_one_file['full_path'])
                logger.info(desc)
            else:
                match_list.append(_file_analysis_info)
                match_info = _file_analysis_info['match']
                desc += '编号({0})：{1}，大小：{2} ==>'.format(match_info['rule']['field'], match_info['num'],
                                                        human_size(_one_file['size']))
                if match_info['dbdata'] is None:
                    match_not_db_list.append(_file_analysis_info)
                    logger.info('%s未找到数据库匹配项，已跳过。', desc)
                    self.cache_file(_one_file['full_path'])
                    continue

                _file_analysis_info['md5'] = file_hash(_file_analysis_info['full_path'])
                match_db_list.append(_file_analysis_info)
                logger.info('%s正在处理入库。', desc)
                if self._resource_storage_way == 'api':
                    self.resource_add_by_api(desc, _file_analysis_info)
                else:
                    self.resource_add_by_db(desc, _file_analysis_info)

        end_ts = now_ts_s()
        elapsed_td = second_2_td(end_ts - self._start_ts)

        summary = "扫描文件夹 {}，分析了 {} 个文件，匹配 {} 个，不匹配 {} 个,匹配未入库 {} 个，入库 {} 个。\n总处理大小 {}。任务开始于：{}，总耗时：{}。{}".format(
            self._folder_path,
            folder_total_file_count,
            len(match_list),
            len(no_match_list),
            len(match_not_db_list),
            len(match_db_list),
            human_size(
                res_total_size),
            ts_2_d(self._start_ts),
            elapsed_td,
            '' if len(match_db_list) == folder_total_file_count else '\n\n其中待处理文件如下：\n{}'.format(
                '\n'.join(
                    list(map(
                        lambda v: v[
                            'origin_name'],
                        match_not_db_list + no_match_list
                    )))
            ))
        logger.info(summary)

        if self._message:
            send_wechat(self._jsd_key, "扫描磁盘资源并入库完成。", summary)

        if self._copy_target_path == '':
            logger.info("请把 %s 的目录的成功处理的文件复制或移动到对应的Web资源目录。成功的文件有：%s", self._folder_path,
                        '、'.join(
                            map(lambda y: y['origin_name'], match_db_list)))
        pass


if __name__ == '__main__':
    ScanOneFolderRes().scan_folder()
    pass
