#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
   created     ： The Jan 26 6:28 PM 2021
   filename    ： main.py
   author      :  Leon
   email       :  silenceace@gmail.com
   Description :
"""
__author__ = 'Leon'

import sys, os
from config import (global_config, config_ini_path, config_json_path)
from scan_res import ScanResource
from folder_create import FolderCreate
from folder_check import FolderChecker
from scan_folder_and_copy_to import ScanFolderAndCopyTo
from scan_one_folder_res import ScanOneFolderRes
from batch_upload_xls import  BatchUploadXls
from import_storage_table_convert import StorageXlsConvert
from import_coll_table_convert import CollXlsConvert
from common import util, FileUtil
import subprocess


def run():
    a = """
 .----------------.  .----------------.  .----------------.  .----------------.
| .--------------. || .--------------. || .--------------. || .--------------. |
| |  ___  ____   | || |   _____      | || | _____  _____ | || |   ______     | |
| | |_  ||_  _|  | || |  |_   _|     | || ||_   _||_   _|| || |  |_   _ \    | |
| |   | |_/ /    | || |    | |       | || |  | | /\ | |  | || |    | |_) |   | |
| |   |  __'.    | || |    | |   _   | || |  | |/  \| |  | || |    |  __'.   | |
| |  _| |  \ \_  | || |   _| |__/ |  | || |  |   /\   |  | || |   _| |__) |  | |
| | |____||____| | || |  |________|  | || |  |__/  \__|  | || |  |_______/   | |
| |              | || |              | || |              | || |              | |
| '--------------' || '--------------' || '--------------' || '--------------' |
 '----------------'  '----------------'  '----------------'  '----------------'

资源扫描使用前，请先确认 config.ini、config.json 配置。

功能列表：
 0.扫描前检查
 1.本地扫描并入库
 2.重设所有藏品封面
 3.显示所有博物馆信息
 4.显示所有用户信息
 5.显示该馆藏品、资源统计
 6.读取表格批量生成目录
 7.检查资源文件夹情况
 8.删除失败的数字资源记录

 e1.扫描根目录所有文件夹并复制指定格式文件到输出目录
 e2.扫描同一个文件夹的所有匹配的资源文件，并根据规则入库到对应的资源库
 e3:上传数据表格到系统
 e4:一普数据表格转换为藏品批量导入表格
 e5:提取数据表格库房信息列转换为柜架导入表格

 p1.打开config.ini配置文件
 p2.打开config.json配置文件
 p3.打开日志文件夹
        """
    print(a)

    common_start_confirm = global_config.config['common'].getboolean('start_confirm')
    common_choice_num = global_config.config['common'].get('choice_num')

    choice_function = None

    if common_choice_num == '-1' and choice_function is None:
        choice_function = input('请选择:')
    elif choice_function is None:
        choice_function = common_choice_num

    scan_res = None

    if choice_function in list(map(lambda x: str(x), range(9))): scan_res = ScanResource()

    if choice_function == '0':
        scan_res.start_check()
    elif choice_function == '1':
        if common_start_confirm:
            print("\n配置信息：\n" + scan_res.config_desc())
            _tmp = input('请确认如上配置，输入任意字符开始:')
            if len(_tmp) > 0:  scan_res.scan_local_storage()
        else:
            scan_res.scan_local_storage()
    elif choice_function == '2':
        scan_res.set_all_cover()
    elif choice_function == '3':
        util.print_data_list(scan_res.db.all_museum(), {'id': 'ID', 'num': '编号', 'name': '名称'})
    elif choice_function == '4':
        util.print_data_list(scan_res.db.all_user(),
                             {'id': 'ID', 'mname': '博物馆名称', 'mid': '博物馆ID', 'real_name': '姓名', 'email': '邮件',
                              'phone': '手机号'})
    elif choice_function == '5':
        print("博物馆信息：", util.print_data_one(scan_res.db.museum_one(scan_res.mid)))
        print("有效藏品数量：{}".format(scan_res.db.museum_coll_count(scan_res.mid)))
        print("藏品资源统计：")
        util.print_data_list(scan_res.db.museum_resource_stat(scan_res.mid),
                             {'cate': '资源类型', 'count': '数量', 'size': '总大小'})
    elif choice_function == '6':
        FolderCreate.show_option_start()
    elif choice_function == '7':
        FolderChecker.show_option_start()
    elif choice_function == '8':
        print("清除失败资源数量：", scan_res.db.del_fail_resource())
    elif choice_function == 'e1':
        _scan_folder_copy_to = ScanFolderAndCopyTo()
        print("\n配置信息：\n" + _scan_folder_copy_to.config_desc())
        input('请确认如上配置，按任意键开始:')
        _scan_folder_copy_to.scan_folder()
    elif choice_function == 'e2':
        _scan_one_folder_res = ScanOneFolderRes()
        print("\n配置信息：\n" + _scan_one_folder_res.config_desc())
        input('请确认如上配置，按任意键开始:')
        _scan_one_folder_res.scan_folder()
    elif choice_function == 'e3':
         BatchUploadXls.show_option_start()
    elif choice_function == 'e4':
         CollXlsConvert.show_option_start()
    elif choice_function == 'e5':
         StorageXlsConvert.show_option_start()

    elif choice_function == 'p1':
        print(file_text_show(config_ini_path))
    elif choice_function == 'p2':
        print(file_text_show(config_ini_path))
    elif choice_function == 'p3':
        log_path = os.path.join(os.getcwd(), 'logs')
        if os.name == "nt":
            os.system("explorer.exe %s" % log_path)
        else:
            print('log日志所在路径：{}。请自行进入。'.format(log_path))
    else:
        print('没有此功能')

    if_continue = input('\n\n是否继续执行？(Y/n)：')
    if str(if_continue).lower() == 'y':
        run()
    else:
        sys.exit(1)


def file_text_show(file_path):
    return '内容如下：\n{1}\n\n文件路径：{0}\n'.format(file_path, FileUtil.readFile(file_path))


if __name__ == '__main__':
    run()
