#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
   created     ： The Jan 26 6:28 PM 2021
   filename    ： util.py
   author      :  Leon
   email       :  silenceace@gmail.com
   Description :
"""
__author__ = 'Leon'

import json
import shutil

import requests
import urllib.parse
import os
import time
import re
import hashlib
import random
import string
import mimetypes
import urllib.parse
from datetime import datetime
from datetime import timedelta

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2227.1 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2227.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2227.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2226.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 6.4; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2225.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2225.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 5.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2224.3 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/40.0.2214.93 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/37.0.2062.124 Safari/537.36",
    "Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/37.0.2049.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 4.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/37.0.2049.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/36.0.1985.67 Safari/537.36",
    "Mozilla/5.0 (Windows NT 5.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/36.0.1985.67 Safari/537.36",
    "Mozilla/5.0 (X11; OpenBSD i386) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/36.0.1985.125 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/36.0.1944.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 5.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.3319.102 Safari/537.36",
    "Mozilla/5.0 (Windows NT 5.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.2309.372 Safari/537.36",
    "Mozilla/5.0 (Windows NT 5.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.2117.157 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.47 Safari/537.36",
    "Mozilla/5.0 (Windows NT 5.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/34.0.1866.237 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/34.0.1847.137 Safari/4E423F",
    "Mozilla/5.0 (Windows NT 5.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/34.0.1847.116 Safari/537.36 Mozilla/5.0 (iPad; U; CPU OS 3_2 like Mac OS X; en-us) AppleWebKit/531.21.10 (KHTML, like Gecko) Version/4.0.4 Mobile/7B334b Safari/531.21.10",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/33.0.1750.517 Safari/537.36",
    "Mozilla/5.0 (Windows NT 6.2; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/32.0.1667.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/32.0.1664.3 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_8_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/32.0.1664.3 Safari/537.36",
    "Mozilla/5.0 (Windows NT 5.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/31.0.1650.16 Safari/537.36",
    "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/31.0.1623.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/30.0.1599.17 Safari/537.36",
    "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/29.0.1547.62 Safari/537.36",
    "Mozilla/5.0 (X11; CrOS i686 4319.74.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/29.0.1547.57 Safari/537.36",
    "Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/29.0.1547.2 Safari/537.36",
    "Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/28.0.1468.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 6.2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/28.0.1467.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 6.2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/28.0.1464.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/27.0.1500.55 Safari/537.36",
    "Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/27.0.1453.93 Safari/537.36",
    "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/27.0.1453.93 Safari/537.36",
    "Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/27.0.1453.93 Safari/537.36",
    "Mozilla/5.0 (Windows NT 5.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/27.0.1453.93 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_8_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/27.0.1453.93 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_7_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/27.0.1453.93 Safari/537.36",
    "Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/27.0.1453.90 Safari/537.36",
    "Mozilla/5.0 (X11; NetBSD) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/27.0.1453.116 Safari/537.36",
    "Mozilla/5.0 (X11; CrOS i686 3912.101.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/27.0.1453.116 Safari/537.36",
    "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.17 (KHTML, like Gecko) Chrome/24.0.1312.60 Safari/537.17",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_8_2) AppleWebKit/537.17 (KHTML, like Gecko) Chrome/24.0.1309.0 Safari/537.17",
    "Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/537.15 (KHTML, like Gecko) Chrome/24.0.1295.0 Safari/537.15",
    "Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/537.14 (KHTML, like Gecko) Chrome/24.0.1292.0 Safari/537.14"
]


def is_match(txt, pattern):
    try:
        return re.search(pattern, txt, re.IGNORECASE) is not None
    except Exception:
        return False


# 正则获取匹配分组  func(..,..).groups()、func(...,...).group('name')
def match_group(txt, pattern):
    return re.match(pattern, txt)


def parse_json(s):
    begin = s.find('{')
    end = s.rfind('}') + 1
    return json.loads(s[begin:end])


def make_dirs(dir_path, del_exist=False):
    if os.path.isdir(dir_path):
        if os.path.exists(dir_path) and del_exist:
            shutil.rmtree(dir_path)
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)


def remove_file(file_path):
    if not os.path.exists(file_path):
        return
    if os.path.isfile(file_path):
        os.remove(file_path)
    elif os.path.isdir(file_path):
        shutil.rmtree(file_path, True)


def get_random_useragent():
    """生成随机的UserAgent
    :return: UserAgent字符串
    """
    return random.choice(USER_AGENTS)


def wait_some_time():
    time.sleep(random.randint(100, 300) / 1000)


def send_wechat(jsd_key, title, message):
    """推送信息到微信"""
    url = 'http://push.ijingniu.cn/send'
    payload = {
        "key": jsd_key,
        "head": title,
        "body": message
    }
    urllib.parse.urlencode(payload)
    headers = {
        'User-Agent': get_random_useragent()
    }
    requests.request(url=url, method='POST', data=payload, headers=headers)


def response_status(resp):
    if resp.status_code != requests.codes.OK:
        print('Status: %u, Url: %s' % (resp.status_code, resp.url))
        return False
    return True


def file_hash(file_path, Bytes=1024):
    """
    计算文件md5
    :param file_path: 文件路径
    :param Bytes: 可不传
    :return: 返回文件MD5字符串
    """
    md5_1 = hashlib.md5()
    with open(file_path, 'rb') as f:
        while 1:
            data = f.read(Bytes)
            if data:
                md5_1.update(data)
            else:
                break
    ret = md5_1.hexdigest()
    return ret


def search_files(root, ext_list=None, file_list=None, deep_search=None):
    """
    搜索目录指定文件
    :param root: 搜索根目录
    :param ext_list: 搜索的后缀列表，后缀请用小写，如：['jpg', 'bmp'] 或 "*"(匹配所有文件)
    :param file_list: 留空
    :return:返回文件对象集合
    """
    if file_list is None:
        file_list = []
    if ext_list is None:
        return file_list
    if deep_search is None:
        deep_search = True

    if not os.path.exists(root):
        return file_list

    items = os.listdir(root)
    for item in items:
        path = os.path.join(root, item)
        if os.path.isdir(path) and deep_search:
            search_files(path, ext_list, file_list)
        elif (type(ext_list) == str and ext_list == '*') or \
                arr_index(ext_list, os.path.splitext(item)[1].lower()[1:]) >= 0:
            file_list.append(file_info(path))
    return file_list


def url_with_ext(url, ext_list):
    """
    判断url后缀是否以列表后缀列表结尾
    :param url: 待后缀的url
    :param ext_list: 格式如：jpg,jpeg,png,bmp
    :return: 返回布尔值
    """
    return ext_list is not None and arr_index(ext_list.split(','),
                                              os.path.splitext(url)[1].lower()[1:]) >= 0


def arr_index(arr, item):
    try:
        return arr.index(item)
    except ValueError:
        return -1


def str_index(str_value, keyword, start=0):
    try:
        return str_value.index(keyword, start)
    except ValueError:
        return -1


def distinctList(origin_list):
    if origin_list is None or len(origin_list) == 0:
        return origin_list

    temp_list = []
    for item in origin_list:
        if not item in temp_list:
            temp_list.append(item)
    return temp_list


def file_info(file_path):
    origin_name = os.path.split(file_path)[1]
    dir_path = os.path.split(file_path)[0]
    ext = os.path.splitext(file_path)[1].lower()[1:]
    return dict(
        name=origin_name[0: len(origin_name) - len(ext) - 1], origin_name=origin_name,
        size=os.path.getsize(file_path), ext=ext, mime=file_mime(file_path),
        create_time=file_create_ts(file_path), dir_path=dir_path,
        dir_name=os.path.split(dir_path)[1], full_path=file_path
    )


def file_mime(url):
    ext = os.path.splitext(url)[1].lower()[1:]
    if ext == "cr2":
        return "image/x-canon-cr2"
    return mimetypes.guess_type(url)[0]


def file_create_ts(file_path):
    """
    获取文件创建时间戳
    :param file_path: 文件路径
    :return:
    """
    return int(os.path.getctime(file_path))


def now_d_str(d_format=None):
    """
    获取当前时间字符串
    :param d_format:
    :return:
    """
    return ts_2_d_str(now_ts_s(), d_format)


def ts_2_d_str(ts_s, d_format=None):
    """
    秒时间戳转时间格式
    :param ts_s:秒 时间戳
    :return:
    """
    time_struct = time.localtime(ts_s)
    return time.strftime('%Y-%m-%d %H:%M:%S' if d_format is None else d_format, time_struct)


def ts_2_d(ts_s):
    return datetime.fromtimestamp(ts_s)


def human_size(size):
    """
    递归实现，精确为最大单位值 + 小数点后三位
    :param size: 字节大小
    :return:
    """

    def strofsize(file_size, file_remainder, unit_level):
        if file_size >= 1024:
            file_remainder = file_size % 1024
            file_size //= 1024
            unit_level += 1
            return strofsize(file_size, file_remainder, unit_level)
        else:
            return file_size, round(file_remainder / 1024, 2), unit_level

    units = ['B', 'KB', 'MB', 'GB', 'TB', 'PB']
    integer, remainder, level = strofsize(size, 0, 0)
    if level + 1 > len(units):
        level = -1
    return '{} {}'.format(integer + remainder, units[level])


def rand_code(num):
    # 生成随机数
    salt = ''.join(random.sample(string.ascii_letters + string.digits, num))
    return salt


def second_2_td(second):
    """
    秒转时分秒
    :param second:
    :return: 返回格式如：0:11:06
    """
    return str(timedelta(seconds=second))


def now_ts_s():
    # 秒时间戳
    return int(time.time())


def now_ts_m():
    # 毫秒时间戳
    return int(time.time() * 1000)


def sub_dirs(root_path):
    """
    获取子文件夹
    :param root_path: 根文件夹
    :return:
    """
    if not os.path.exists(root_path):
        return None
    # 获取该目录下的所有文件或文件夹目录
    files = os.listdir(root_path)
    dir_list = []  # 声明list
    for file in files:
        # 得到该文件下所有目录的路径
        m = os.path.join(root_path, file)
        # 判断该路径下是否是文件夹
        if os.path.isdir(m):
            h = os.path.split(m)
            dir_list.append(dict(dir_name=h[1], dir_path=m))
    return dir_list


def print_data_list(db_list, key_names=None):
    """
    打印数据库集
    :param db_list: 数据集记录
    :param key_names: key格式化名称dict
    :return:
    """
    if db_list is None or len(db_list) == 0:
        print('无数据')
        return

    for idx, item in enumerate(db_list):
        print('序号.{} ==>'.format(str(idx + 1)), print_data_one(item, key_names))


def print_data_one(db_one, key_names=None):
    if db_one is None:
        print('无数据')
        return
    keys = db_one.keys()
    return '、'.join(
        list(map(
            lambda v: "{}：{}".format(v if key_names is None or v not in key_names.keys() else key_names[v],
                                     db_one[v]),
            keys)))


def search_depth_sub_dirs(root,  depth=None, dir_list=None):
    """
    根据深度搜索目标文件夹
    :param root: 开始的根目录
    :param depth: 搜索深度，只获取最高深度的路径 如: depth=2 文件夹：a>b>c 那获取的路径为： /a/b/c ,不包含 /a/b
    :param dir_list: 获取的文件夹列表
    :return:返回文件对象集合
    """
    if dir_list is None:
        dir_list = []
    if depth is None:
        depth = 1

    if not os.path.exists(root):
        return dir_list

    items = os.listdir(root)
    for item in items:
        path = os.path.join(root, item)
        if not os.path.isdir(path):
            continue
        if depth > 1:
            search_depth_sub_dirs(path, depth - 1, dir_list)
        elif depth == 1:
            dir_list.append(path)
    return dir_list
    

if __name__ == '__main__':
    print("hello world")
    # print(is_match("0005_NKⅢ：710_00", "^(?P<num>\d+)[\_\-](?P<name>.+)$"))
