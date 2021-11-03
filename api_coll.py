#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
   created     ： The Jan 31 9:29 PM 2021
   filename    ： api_coll.py
   author      :  Leon
   email       :  silenceace@gmail.com
   Description :
"""
__author__ = 'Leon'

import os
import requests
from common import PException
from common.logger import logger
from config import global_config, coll_api_paths
from common import util
import json


class ApiColl:
    """
    藏品系统API操作
    """

    def __init__(self, base_url=None, login_user=None, login_pwd=None):
        if base_url is None:
            base_url = global_config.config['coll']['api_base_url']

        if login_user is None:
            login_user = global_config.config['coll']['sys_login_user_name']

        if login_pwd is None:
            login_pwd = global_config.config['coll']['sys_login_user_password']

        self._api_base_url = base_url
        self._user_name = login_user
        self._password = login_pwd
        self.token = None
        self.session_user = self.user_login()
        pass

    def request(self, method=None, url_path=None, params=None, headers=None, files=None, json_obj=None, data_obj=None,
                timeout=None):
        """"
        封装请求
        """
        if method is None:
            method = 'POST'

        if timeout is None:
            timeout = 60

        if params is None:
            params = dict(ts=util.now_ts_s())

        if headers is None:
            headers = dict()
            headers['Content-Type'] = 'application/json'

        headers['X-Auth-Token'] = self.token

        try:
            rpe = requests.request(method=method, url=self._api_base_url + url_path, data=data_obj,
                                   params=params, headers=headers, files=files, json=json_obj, timeout=timeout)
            if rpe.status_code != 200:
                logger.error("网络请求失败==>%s", rpe.text)
                return None
            else:
                response_obj = json.loads(rpe.text)
                if not response_obj.get('success'):
                    logger.error("数据交互遇到错误：%s", "、".join(response_obj['errors']))
                    return None
                else:
                    return response_obj.get('data')
        except Exception as err:
            logger.error("API请求遇到网络错误: %s", err)
            return None

    def user_login(self):
        """
        用户登陆
        """
        json_obj = {
            'userName': self._user_name,
            'password': self._password,
            'rememberMe': True
        }
        rlt = self.request(url_path=coll_api_paths['user']['login'], json_obj=json_obj, timeout=3)
        if rlt is None:
            raise PException("用户登陆失败，请检查用户名密码是否正确！")

        self.token = rlt['userToken']
        return rlt

    def storage_simple_list(self, mid):
        """
        获取建库房列表信息
        """
        rlt = self.request(url_path=coll_api_paths['storage']['storage_simple_list'].format(mid), method='GET', timeout=3)
        if rlt is None:
            return None
        return rlt.get('list')
        pass

    def upload_img(self, img_path=None):
        """
        普通上传图片接口
        """
        if not os.path.exists(img_path):
            logger.error("%s 此文件不存在，无法上传", img_path)
            return None
        if not util.is_img(img_path):
            logger.error("%s 不是图片文件", img_path)
            return None

        rlt = self.request(url_path=coll_api_paths['upload']['img'], headers=dict(),
                           files={'file': open(img_path, 'rb')})
        if rlt is None:
            return None
        return rlt.get('info')
        pass

    def check_xls_file(self, file_path=None):
        if not os.path.exists(file_path):
            logger.error("%s 此文件不存在，无法上传", file_path)
            return None
        file_info = util.file_info(file_path)

        if file_info.get('ext') not in ['xls', 'xlsx']:
            logger.error("%s 请上传XLS数据", file_path)
            return None
        return file_info

    def coll_table_upload(self, mid, file_path=None):
        """
        导入藏品信息表格
        :param mid: 博物馆ID
        :return:
        """
        xls_info = self.check_xls_file(file_path)
        if xls_info is None:
            return None
        rlt = self.request(url_path=coll_api_paths['collection']['coll_table_upload'].format(mid), headers=dict(),
                           files={'file': open(file_path, 'rb')}, timeout=7200)
        if rlt is None:
            return None
        return rlt.get('info')
        pass

    def coll_storage_table_upload(self, mid, file_path=None):
        """
        导入藏品柜架信息
        :param mid: 博物馆ID
        :return:
        """
        xls_info = self.check_xls_file(file_path)
        if xls_info is None:
            return None
        rlt = self.request(url_path=coll_api_paths['collection']['coll_storage_table_upload'].format(mid),
                           headers=dict(),
                           files={'file': open(file_path, 'rb')}, timeout=7200)
        if rlt is None:
            return None
        return rlt.get('info')
        pass

    def resource_upload(self, coll_id, cate=None, file_path=None):
        """
        藏品资源文件上传
        """
        if not os.path.exists(file_path):
            logger.error("%s 此文件不存在，无法上传", file_path)
            return None
        if cate is None:
            cate = 'IMAGE'

        rlt = self.request(url_path=coll_api_paths['resource']['upload'].format(coll_id, cate), headers=dict(),
                           files={'file': open(file_path, 'rb')}, timeout=180)
        if rlt is None:
            return None
        return rlt.get('info')
        pass

# api = ApiColl()
# # api.user_login()
# api.resource_upload(coll_id=10, file_path='/Users/potato/Pictures/potato.jpg')
