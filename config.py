#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
   created     ： The Jan 28 5:50 PM 2021
   filename    ： config.py
   author      :  Leon
   email       :  silenceace@gmail.com
   Description :  配置
"""
__author__ = 'Leon'

import os
import json
import shutil
import configparser

_TML_CONFIG_INI_PATH = os.path.join(os.getcwd(), 'config.sample.ini')
_TML_CONFIG_JSON_PATH = os.path.join(os.getcwd(), 'config.sample.json')

config_ini_path = os.path.join(os.getcwd(), 'config.ini')
config_json_path = os.path.join(os.getcwd(), 'config.json')


class Config(object):
    def __init__(self, config_infi_file_path):
        self._path = config_infi_file_path
        if not os.path.exists(self._path):
            shutil.copy(_TML_CONFIG_INI_PATH, self._path)

        if not os.path.exists(self._path):
            raise FileNotFoundError("No such file: {}".format(config_infi_file_path))

        self.config = configparser.ConfigParser()
        self.config.read(self._path, encoding='utf-8-sig')
        self.configRaw = configparser.RawConfigParser()
        self.configRaw.read(self._path, encoding='utf-8-sig')

    def get(self, section, name):
        return self.config.get(section, name)

    def get_raw(self, section, name):
        return self.configRaw.get(section, name)


global_config = Config(config_ini_path)

# 读取config.json对象
if not os.path.exists(config_json_path):
    shutil.copy(_TML_CONFIG_JSON_PATH, config_json_path)

json_config = json.loads(open(config_json_path, mode='r', encoding='utf-8').read())
scan_config = json_config['scan_config']  # 扫描配置
coll_api_paths = json_config['coll_api_paths']  # coll api path配置
folder_check_config = json_config['folder_check_config']  # 文件夹检查配置

# 获取文件夹文件名编号规则配置
get_res_num_rules = list(filter(lambda v: v['enable'], json_config["get_res_num_rules"]))
# 根据order字段进行排序 升序
sorted(get_res_num_rules, key=lambda s: s['order'])

# 获取各资源类型配置所对应的文件扩展名
resource_cate_ext_list = json_config["resource_cate_ext_list"]

# 表格转换配置
execl_convert_set = json_config["execl_convert"]

# 藏品资源类型配置对象
resource_cate_ext_config = dict()
for resource_cate_ext_item in resource_cate_ext_list:
    resource_cate_ext_config[resource_cate_ext_item['cate']] = resource_cate_ext_item

# 藏品编号所对应的数据库字段名称
coll_info_num_field_set = dict(
    regNum='c_register_num',  # 总登记号
    cateNum='c_cate_num',  # 分类号
    oldNum='c_old_num',  # 旧号
    otherNum='c_other_code', # 其他号
    collectionNum='c_collection_num',  # 入馆凭证号
    comeNum='c_come_num'  # 入馆登记号
)
