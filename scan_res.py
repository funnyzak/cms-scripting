#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
   created     ： The Jan 15 6:28 PM 2021
   filename    ： scan_res.py
   author      :  Leon
   email       :  silenceace@gmail.com
   Description :  扫描藏品资源文件夹下子业务目录，并分别扫描业务目录数据并入库资源信息
"""
__author__ = 'Leon'

import os
import json
from database import DataBase
from config import (global_config, scan_config)
from functools import reduce
import shutil
from api_coll import ApiColl
from common import (ZipUtil, new_logger, PException)
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
    distinctList,
    search_depth_sub_dirs
)
from common.imgutil import (
    img_exif,
    is_img,
    is_photo,
    img_compress,
    img_size
)

LOGGER_FILE_NAME = 'scan_res_{}.log'.format(str(now_ts_s()))
logger = new_logger(LOGGER_FILE_NAME)


class ScanResource:
    """
    扫描并入库等操作文件夹资源
    """

    def __init__(self):
        self.coll_api = ApiColl()
        self.session = self.coll_api.session_user
        self.mid = self.session['user']['mid']
        self.uid = self.session['user']['id']
        self.db = DataBase(self.uid, self.mid)
        self.db.re_connect()
        self.scan_config = scan_config
        self._start_ts = now_ts_s()
        self._scan_type_list = global_config.get_raw(
            'scan_res', 'go_scan_type_list').split(' ')
        self._root_path = global_config.get_raw('scan_res', 'root_path')
        self._depth = global_config.config['scan_res'].getint('depth')

        # 根据根目录和深度获取所有有资源数据的父级文件夹
        _tmp_root_dirs = []
        for _dir in self._root_path.split():
            if not os.path.exists(_dir):
                continue
            _tmp_root_dirs.extend([_dir] if self._depth <= 1 else search_depth_sub_dirs(
                _dir, self._depth))

        self._root_dirs = _tmp_root_dirs

        self._set_collection_cover_res_idx = global_config.config['scan_res'].getint(
            'set_collection_cover_res_idx')
        self._set_collection_cover_res_format = global_config.get_raw(
            'scan_res', 'set_collection_cover_res_format')
        self._copy_target_path = global_config.get_raw(
            'scan_res_common', 'copy_target_path')
        self._copy_target_path_rename = global_config.config['scan_res_common'].getboolean(
            'copy_target_path_rename')
        self._check_rule_cate_same_res_count_ignore = global_config.config['scan_res'].getboolean(
            'check_rule_cate_same_res_count_ignore')
        self._copy_target_path_to_compress = global_config.config['scan_res_common'].getboolean(
            'copy_target_path_to_compress')
        self._copy_target_path_to_compress_quality = global_config.config['scan_res_common'].getint(
            'copy_target_path_to_compress_quality')
        self._copy_target_path_to_compress_scale_precent = global_config.config['scan_res_common'].getint(
            'copy_target_path_to_compress_scale_precent')
        self.select_coll_info_where_field_name = global_config.get_raw(
            'scan_res', 'select_coll_info_where_field_name')
        self._match_dir_pattern = global_config.get_raw(
            'scan_res', 'match_dir_pattern')
        self._auto_create_coll_info = global_config.config['scan_res'].getboolean(
            'auto_create_coll_info')
        self._resource_url_prefix = global_config.get_raw(
            'scan_res_common', 'resource_url_prefix')
        self._resource_storage_way = global_config.get_raw(
            'scan_res_common', 'resource_storage_way')
        self._check_rule_check_3d_dir_name_pattern = global_config.get_raw('scan_res',
                                                                           'check_rule_check_3d_dir_name_pattern')
        self._message = global_config.config['messenger'].getboolean('enable')
        self._jsd_key = global_config.get_raw('messenger', 'jsdkey')

        _sub_dir_list_rlt = self.get_data_item_dirs()
        self.sub_dir_list = [] if _sub_dir_list_rlt is None else _sub_dir_list_rlt['list']
        self.sub_dir_list_no_match = [
        ] if _sub_dir_list_rlt is None else _sub_dir_list_rlt['no_match']

        if self._resource_storage_way == 'db' and self._copy_target_path != '' and not os.path.exists(
                self._copy_target_path):
            logger.info("创建资源目标文件夹：%s\n", self._copy_target_path)
            os.makedirs(self._copy_target_path)
        pass

    def get_data_item_dirs(self):
        """
        获取所有待处理的资源文件夹
        """
       # 遍历父文件夹获取所有的资源文件夹
        _sub_dir_list_rlt = dict(list=[], no_match=[])
        for _dir in self._root_dirs:
            _data_dirs = self.get_subdir_from_root(_dir)
            if _data_dirs is None:
                continue

            _sub_dir_list_rlt['list'].extend(_data_dirs['list'])
            _sub_dir_list_rlt['no_match'].extend(_data_dirs['no_match'])

        return _sub_dir_list_rlt

    @classmethod
    def scan_config_desc(cls, scan_config):
        return '\n'.join(
            list(
                map(
                    lambda v: "【{}】扫描方式：从业务文件夹的【{}】目录下，搜索所有的：【{}】格式。".format(scan_config[v]['name'],
                                                                             '、'.join(
                                                                                 scan_config[v][
                                                                                     'dir_name_list']),
                                                                             '、'.join(
                                                                                 [] if scan_config[v][
                                                                                     'ext_list'] is None else
                                                                                 scan_config[v]['ext_list'])),
                    scan_config.keys())
            )
        )

    def config_desc(self):
        """
        打印配置
        """
        con_desc = "\nDB Host：{}\n".format(
            global_config.get_raw('db', 'mysql_host'))
        con_desc += "DB Port：{}\n".format(
            global_config.get_raw('db', 'mysql_port'))
        con_desc += "DB Database：{}\n".format(
            global_config.get_raw('db', 'mysql_database'))
        con_desc += "DB User：{}\n".format(
            global_config.get_raw('db', 'mysql_user'))
        con_desc += "DB Password：{}\n".format(
            global_config.get_raw('db', 'mysql_password'))
        con_desc += "API Base URL：{}\n".format(
            global_config.get_raw('coll', 'api_base_url'))
        con_desc += "系统登陆用户信息：{}\n".format(json.dumps(
            self.session['user'], ensure_ascii=False))
        con_desc += "自动创建藏品信息：{}\n".format(
            global_config.get_raw('scan_res', 'auto_create_coll_info'))
        con_desc += "扫描资源目录：{}\n".format(
            global_config.get_raw('scan_res', 'root_path'))
        con_desc += "资源入库方式：{}\n".format(global_config.get_raw(
            'scan_res_common', 'resource_storage_way'))
        con_desc += "入库资源输出目录：{}\n".format(
            global_config.get_raw('scan_res_common', 'copy_target_path'))
        con_desc += "入库资源时资源是否重命名：{}\n".format(global_config.get_raw(
            'scan_res_common', 'copy_target_path_rename'))
        con_desc += "入库资源时资源是否对资源进行压缩：{}\n".format(
            global_config.get_raw('scan_res_common', 'copy_target_path_to_compress'))
        con_desc += "入库资源时资源压缩百分比：{}\n".format(
            global_config.get_raw('scan_res_common', 'copy_target_path_to_compress_scale_precent'))
        con_desc += "入库资源时资源压缩质量：{}\n".format(
            global_config.get_raw('scan_res_common', 'copy_target_path_to_compress_quality'))
        con_desc += "搜索3D模型文件夹时的正则匹配：{}\n".format(
            global_config.get_raw('scan_res', 'check_rule_check_3d_dir_name_pattern'))
        con_desc += "文物资源目录文件如果<=对应数据库资源数量则忽略：{}\n".format(
            global_config.config['scan_res'].getboolean('check_rule_cate_same_res_count_ignore'))
        con_desc += "资源URL前缀：{}\n".format(global_config.get_raw(
            'scan_res_common', 'resource_url_prefix'))
        con_desc += "要扫描资源类型：{}\n".format(
            ' '.join(list(map(lambda x: self.scan_config[x]['name'], self._scan_type_list))))
        con_desc += "获取匹配操作文件夹的正则表达式：{}\n".format(
            global_config.get_raw('scan_res', 'match_dir_pattern'))
        con_desc += "获取编号匹配数据库字段：{}\n".format(global_config.get_raw(
            'scan_res', 'select_coll_info_where_field_name'))
        con_desc += "资源URL前缀：{}\n".format(global_config.get_raw(
            'scan_res_common', 'resource_url_prefix'))
        con_desc += "资源搜索方式：{}\n".format(
            self.scan_config_desc(self.scan_config))
        con_desc += "资源搜索配置：{}\n".format(
            json.dumps(self.scan_config, ensure_ascii=False))
        return con_desc
        pass

    def start_check(self):
        if len(self._root_dirs) == 0:
            raise PException("扫描资源目录不存在，请检查")
        if self.session['user']['mid'] is None:
            raise PException('请登陆博物馆管理账户')
        if len(self.sub_dir_list) == 0:
            raise PException("未找到匹配的待处理文件夹。")

        logger.info("配置信息：%s", self.config_desc())

        logger.info("文件夹过滤后，找到符合 %s 名称规则的文件夹有 %s 个，分别是：\n%s。 \n\n共%s个。 \n不符合的文件夹有 %s 个，分别是：\n%s。\n\n共%s个",
                    self._match_dir_pattern, len(self.sub_dir_list),
                    '\n'.join(list(map(lambda v: '文件夹：{} 编号：{} 名称：{}'.format(v['dir_name'],
                                                                             v['num'], v['name']), self.sub_dir_list))),
                    len(self.sub_dir_list),
                    len(self.sub_dir_list_no_match),
                    '无' if len(self.sub_dir_list_no_match) == 0 else '\n'.join(
                        list(map(lambda v: v['dir_name'], self.sub_dir_list_no_match))),
                    len(self.sub_dir_list_no_match)
                    )
        pass

    def set_all_cover(self):
        """
        设置藏品背景图
        :return:
        """
        coll_all = self.db.coll_all()
        if coll_all is None:
            raise PException('数据库未发现藏品信息。')
        for idx, coll in enumerate(coll_all):
            self.db.coll_set_cover(coll['id'], self._set_collection_cover_res_format,
                                   self._set_collection_cover_res_idx)
            logger.info("序号.{0}，藏品ID：{2}, 藏品名：{1} 设置封面任务已执行。".format(
                idx + 1, coll['c_name'], coll['id']))

        msg = "设置藏品信息封面已完成，共设置 {} 个。".format(len(coll_all))
        logger.info(msg)
        if self._message:
            send_wechat(self._jsd_key, msg, msg)
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
            mgs = match_group(dir_one['dir_name'], self._match_dir_pattern)
            if mgs is None:
                no_match_list.append(dir_one)
                continue
            dir_one['num'] = mgs.group('num')
            dir_one['name'] = mgs.group('name')
            dir_one['parent'] = root_path
            match_list.append(dir_one)
            # 判断并加入藏品是否有子组件文件夹
            sub_dir_list = self.get_subdir_from_root(dir_one['dir_path'])
            if sub_dir_list is None:
                continue
            match_list.extend(sub_dir_list['list'])
        return dict(list=match_list, no_match=no_match_list)
        pass

    def get_dir_all_resource(self, dir_info):
        """
        获取文物文件夹对应所有需入库的资源文件
        """
        rlt_list = []

        def f_search_resource(sub_dir, ext_list, cate):
            _tmp_list = search_files(sub_dir, ext_list, [])
            for item in _tmp_list:
                item['cate'] = cate
            return _tmp_list

        for type_name in self._scan_type_list:
            _scan_set = self.scan_config.get(type_name)
            if type_name == 'THREE_MODEL':
                rlt_list += self.get_or_set_dir_3d_resouce(dir_info, _scan_set)
                continue

            if _scan_set.get('dir_name_list') is None or len(_scan_set.get('dir_name_list')) == 0:
                rlt_list += f_search_resource(
                    dir_info.get('dir_path'), _scan_set.get('ext_list'), type_name)
            else:
                for sub_dir_name in _scan_set.get('dir_name_list'):
                    rlt_list += f_search_resource(
                        os.path.join(dir_info.get('dir_path'),
                                     sub_dir_name.replace('/', os.path.sep)),
                        _scan_set.get('ext_list'), type_name)

        return rlt_list
        pass

    def get_or_set_dir_3d_resouce(self, dir_info, scan_set):
        """
        获取或设置3D文件夹的3D文件
        """
        f_list = []
        search_path = []
        if scan_set.get('dir_name_list') is None or len(scan_set.get('dir_name_list')) == 0:
            search_path.append(dir_info.get('dir_path'))
        else:
            search_path = list(
                map(lambda sub_dir_name: os.path.join(dir_info.get('dir_path'), sub_dir_name.replace('/', os.path.sep)),
                    scan_set.get('dir_name_list')))

        obj_files = []
        for _3d_path in search_path:
            if not os.path.exists(_3d_path):
                continue
            obj_files += search_files(_3d_path, ['obj'], [])
        if len(obj_files) == 0:
            return f_list

        match_3d_path_list = list(map(lambda x: x['dir_path'], obj_files))
        # 如果配置3D文件夹搜索则进行匹配
        if self._check_rule_check_3d_dir_name_pattern is not None or len(
                self._check_rule_check_3d_dir_name_pattern) > 0:
            match_3d_path_list = list(
                filter(lambda x: is_match(os.path.split(x)[1], self._check_rule_check_3d_dir_name_pattern),
                       match_3d_path_list))
        if len(match_3d_path_list) == 0:
            return f_list

        distinct_3d_path_list = distinctList(match_3d_path_list)
        for _3d_model_path in distinct_3d_path_list:
            _3d_zip_path = _3d_model_path + '.zip'
            if not os.path.exists(_3d_zip_path):
                logger.info("正在对 %s 进行压缩，输出到：%s。",
                            _3d_model_path, _3d_zip_path)
                try:
                    ZipUtil.add_files_to_zip(_3d_zip_path, _3d_model_path)
                except Exception as err:
                    logger.error("对 %s 进行压缩失败 %s", _3d_model_path, err)
                    continue

            zip_info = file_info(_3d_zip_path)
            zip_info['cate'] = 'THREE_MODEL'
            f_list.append(zip_info)

        return f_list
        pass

    def copy_res_to_target_dir(self, res, dir_info):
        if self._copy_target_path == '':
            return None
        source_path = res['full_path']
        target_path = os.path.join(
            self._copy_target_path, res['full_path'].replace(dir_info['parent'], "")[1:])
        target_dir = target_path[0:len(target_path) - len(res['origin_name'])]
        if self._copy_target_path_rename:
            _file_date = ts_2_d(res['create_time'])
            target_dir = os.path.join(self._copy_target_path, str(self.mid), str(_file_date.year),
                                      str(_file_date.month) + str(_file_date.day))
            target_path = os.path.join(
                target_dir, res['md5'] + '.' + res['ext'])

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

                logger.info("%s已复制%s文件：%s 到目标文件 %s", dir_info['info'], '' if not compress_success else '并压缩',
                            source_path, target_path)
            except Exception as e:
                logger.error("%s复制文件发生意外错误。source:%s, target:%s。错误信息：%s",
                             dir_info['info'], source_path, target_dir, e)
                return None
        return dict(target_dir=target_dir, target_path=target_path)
        pass

    def resource_exist_db_check(self, dir_info, md5s):
        if len(list(filter(lambda x: x['res_md5'] is not None and x['res_md5'] == md5s,
                           dir_info['data_res']))) > 0:
            """
            和数据库资源md5和路径比对，如果已存在则忽略
            """
            logger.info('%s该资源已在库中。无需重复入库。', dir_info['info'])
            return True
        return False

    def resource_add_by_db(self, idx, dir_info, res):
        """
        通过DB的方式，资源直接入库
        """
        save_path = res['full_path'].replace(
            dir_info['parent'], "").replace(os.path.sep, "/")
        url = "{}{}".format(self._resource_url_prefix, save_path)
        res_md5 = res['md5']
        res_size = res['size']
        logger.info("%s资源：%s/%s %s, 大小：%s，源路径：%s。", dir_info['info'], idx + 1, len(dir_info['res_list']),
                    res.get('name'), human_size(res['size']), res.get('full_path'))

        if self._copy_target_path != '':
            _target = self.copy_res_to_target_dir(res, dir_info)
            res['target'] = file_info(_target['target_path'])
            save_path = _target['target_path'].replace(
                self._copy_target_path, '').replace(os.path.sep, "/")
            url = "{}{}".format(self._resource_url_prefix, save_path)
            res_md5 = file_hash(_target['target_path'])
            res_size = res['target']['size']

        if self.resource_exist_db_check(dir_info, res_md5):
            return

        exif_info = None if not is_photo(
            save_path) else img_exif(res['full_path'])  # 原图Exif信息
        ext_str = None if exif_info is None else json.dumps(
            dict(exif=exif_info))

        img_s = img_size(
            res.get('target').get('full_path') if 'target' in res.keys() else res['full_path'])  # 如果复制资源则使用新资源图片否则旧图
        ins_res = {
            'cate': res.get('cate'),
            'name': res.get('name'),
            'relationId': dir_info['data_info']['id'],
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
        logger.info("%s资源：%s/%s %s 已入库。 入库信息：%s。", dir_info['info'], idx + 1, len(dir_info['res_list']),
                    res.get('name'),
                    json.dumps(ins_res)[0:70] + '...')

    def resource_add_by_api(self, idx, dir_info, res):
        """
        通过API的方式上传资源
        """
        logger.info("%s资源：%s/%s %s, 大小：%s，源路径：%s。", dir_info['info'], idx + 1, len(dir_info['res_list']),
                    res.get('name'), human_size(res['size']), res.get('full_path'))
        if self.resource_exist_db_check(dir_info, res['md5']):
            return
        rlt = self.coll_api.resource_upload(
            dir_info['data_info']['id'], res.get('cate'), res['full_path'])
        if rlt is None:
            logger.error("上传资源遇到错误。 资源路径：%s", res['full_path'])
            return
        logger.info("%s资源：%s/%s %s 已入库。 入库信息：%s。", dir_info['info'], idx + 1, len(dir_info['res_list']),
                    res.get('name'),
                    json.dumps(rlt)[0:70] + '...')

    def scan_dir_res_storage(self, dir_info):
        """
        处理扫描出的文物相关资源
        """
        if len(dir_info['res_list']) == 0:
            logger.info("%s在该文件夹未扫到相关资源，已忽略。", dir_info['info'])
            return

        res_count = len(dir_info['res_list'])
        logger.info("%s扫描到 %s 个匹配资源，资源总大小为 %s，路径 %s。 资源分别为：%s",
                    dir_info['info'], res_count, human_size(
                        dir_info['res_size']), dir_info['dir_path'],
                    list(map(lambda x: x['full_path'].replace(dir_info['dir_path'], ''), dir_info['res_list'])))

        for idx, res in enumerate(dir_info['res_list']):
            res['md5'] = file_hash(res['full_path'])
            if self._resource_storage_way == 'api' or res['cate'] == 'THREE_MODEL':
                self.resource_add_by_api(idx, dir_info, res)
            else:
                self.resource_add_by_db(idx, dir_info, res)

        logger.info("%s资源信息已全部入库。", dir_info['info'])
        pass

    def scan_local_storage(self):
        """
        开始扫描文件夹并资源入库
        """
        self.start_check()

        total_dir_count = len(self.sub_dir_list)
        success = 0
        insert_total_count = 0
        res_total_size = 0
        for idx, dir_one in enumerate(self.sub_dir_list):
            one_desc = "序号.{3}【{2}】，提取编号：{0}，提取名称：{1} ===> ".format(
                dir_one.get('num'), dir_one.get('name'), dir_one.get('dir_name'), idx + 1)
            dir_one['index'] = idx + 1
            dir_one['info'] = one_desc

            logger.info("%s原始路径 %s。", one_desc, dir_one.get('dir_path'))

            data_info = self.db.coll_one(
                self.select_coll_info_where_field_name, dir_one.get('num'))
            if data_info is None:
                if not self._auto_create_coll_info:
                    logger.error("%s未找到对应的数据库记录，已跳过处理。\n\n", one_desc)
                    continue
                else:
                    self.db.add_coll_by_dir(
                        self.select_coll_info_where_field_name, dir_one['num'], dir_one['name'])
                    data_info = self.db.coll_one(
                        self.select_coll_info_where_field_name, dir_one.get('num'))
                    logger.info("%s无数据库记录，已自动创建该目录对应藏品信息。", one_desc)

            logger.info("%s从数据库查到该对应数据库记录（ID：%s，名称：%s）。查询原始数据：%s..。", one_desc, data_info['id'], data_info['c_name'],
                        json.dumps(data_info)[0:70])

            dir_one['data_info'] = data_info  # 获取对应的藏品信息
            data_res_list = self.db.coll_res_list(
                dir_one['data_info']['id'], self._scan_type_list)
            # 获取藏品对应的所有资源信息
            dir_one['data_res'] = [] if data_res_list is None else data_res_list
            dir_one['data_res_count'] = 0 if dir_one['data_res'] is None else len(
                dir_one['data_res'])
            logger.info("%s从数据库查到该对应的资源数据已有 %s 条。",
                        one_desc, dir_one['data_res_count'])

            logger.info("%s正在扫描和分析文件夹下数据，请稍候...", one_desc)

            dir_one['res_list'] = self.get_dir_all_resource(
                dir_one)  # 获取并设置文件夹所有匹配资源
            dir_one['res_count'] = len(dir_one['res_list'])  # 资源总数
            if dir_one['res_count'] == 0:
                logger.info("%s未找到可入库资源,已跳过。", one_desc)
                continue

            dir_one['res_size'] = reduce(
                lambda x, y: x + y, list(map(lambda x: x['size'], dir_one['res_list'])))

            success += 1
            insert_total_count += dir_one['res_count']
            res_total_size += dir_one['res_size']
            dir_one['op'] = True

            if dir_one['res_count'] <= dir_one['data_res_count'] and self._check_rule_cate_same_res_count_ignore:
                logger.info("%s数据库已存在该文物资源类型文件数 %s(本地扫描 %s 个)，已忽略。", one_desc, dir_one['data_res_count'],
                            dir_one['res_count'])
                continue

            self.scan_dir_res_storage(dir_one)

            if global_config.config['scan_res'].getboolean('set_collection_cover'):
                self.db.coll_set_cover(dir_one['data_info']['id'], self._set_collection_cover_res_format,
                                       self._set_collection_cover_res_idx)
                logger.info("%s已执行设置资源图到藏品封面。", one_desc)

        end_ts = now_ts_s()
        elapsed_td = second_2_td(end_ts - self._start_ts)

        root_dirs_str = '\t'.join(list(map(lambda v: v,  self._root_dirs)))

        summary = "扫描文件夹 {}，处理了 {} 个文件夹，其中成功 {} 个，待确认 {} 个。 共计入库 {} 个资源, 总处理大小 {}。任务开始于：{}，总耗时：{}。{}".format(
            root_dirs_str,
            total_dir_count,
            success,
            total_dir_count - success,
            insert_total_count,
            human_size(
                res_total_size),
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
            send_wechat(self._jsd_key, "扫描磁盘资源并入库完成。", summary)

        if self._copy_target_path == '':
            logger.info("请把 %s 的目录的成功处理的文件夹复制或移动到对应的Web资源目录。成功的文件夹有：%s", root_dirs_str,
                        '、'.join(
                            map(lambda y: y['dir_name'], list(filter(lambda x: 'op' in x.keys(), self.sub_dir_list)))))
        pass
