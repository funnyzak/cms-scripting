#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
   created     ： The Jan 26 6:28 PM 2021
   filename    ： database.py
   author      :  Leon
   email       :  silenceace@gmail.com
   Description :  操作藏品数据库
"""
__author__ = 'Leon'

import pymysql.cursors
from pymysql import OperationalError

from config import global_config
from common import util


class DataBase:
    def __init__(self, uid=None, mid=None):
        self.uid = uid
        self.mid = mid
        self.conn = self.connect()
        self.curs = self.conn.cursor()

    def connect(self):
        return pymysql.connect(host=global_config.get_raw('db', 'mysql_host'),
                               user=global_config.get_raw('db', 'mysql_user'),
                               port=int(global_config.get_raw('db', 'mysql_port')),
                               password=global_config.get_raw('db', 'mysql_password'),
                               database=global_config.get_raw('db', 'mysql_database'),
                               cursorclass=pymysql.cursors.DictCursor)

    def re_connect(self):
        """ MySQLdb.OperationalError异常"""
        # self.con.close()
        while True:
            try:
                self.conn.ping()
                break
            except OperationalError:
                self.conn.ping(True)

    def add_coll_by_dir(self, numFieldName, numFieldValue, name, otherCodeType):
        """
        根据识别的文件夹创建藏品信息
        :param num 识别文件夹提取的编号
        :param name 识别文件夹提取的名称
        :return: 插入记录
        """
        self.re_connect()
        with self.conn:
            sql = "INSERT INTO `kunlun_collection_login`(`cl_mid`, `c_del`, `c_draft`, `{0}`, `c_name`, `c_info_type`, `c_add_time`, `c_update_time`, `c_update_user`, `c_add_user`, `c_review_status`, `c_status`, `c_other_type`) VALUES ({1}, 0, 0, '{2}', '{3}', 'COLLECTION_LOGIN', {4}, {4}, {5}, {5}, 'WAIT_SUBMIT', 'NO_STORAGE', {6});".format(
                numFieldName, self.mid, numFieldValue, name, util.now_ts_s(), self.uid,  "'{}'".format(otherCodeType) if otherCodeType else 'NULL')
            self.curs.execute(sql)
            self.conn.commit()
        return True

    def coll_one(self, numFieldName, fieldValue, otherCodeType):
        """
        从数据库查询匹配藏品信息
        value: key 对应的值
        return: 成功返回dict,失败返回 None
        """
        self.re_connect()

        extCnd = "AND `c_other_type` = '{}'".format(
            otherCodeType) if otherCodeType else ''

        with self.conn:
            sql = "SELECT * FROM `kunlun_collection_login` WHERE {} = '{}' AND cl_mid = {} {} AND c_info_type = 'COLLECTION_LOGIN' AND c_del = 0 ORDER BY `id` DESC LIMIT 0,1".format(
                numFieldName, fieldValue, self.mid, extCnd)
            self.curs.execute(sql)
            return self.curs.fetchone()

    def coll_set_cover(self, coll_id, img_ext='jpg', res_idx=1):
        """
        设置藏品信息封面
        :param coll_id: 藏品ID
]        :return: 返回成功
        """
        self.re_connect()
        with self.conn:
            sql = "update kunlun_collection_login set c_cover = (select res_key from potato_resource_info WHERE " \
                  "`res_del` = 0 AND `res_status` = 'SUCCESS' AND `res_belong_type` = 'COLLECTION_LOGIN_INFO' AND " \
                  "`res_relation_id` = {0} AND `res_suffix` = '{1}' AND `res_cate` = 'IMAGE' limit {2},1) where " \
                  "`id` = {0} AND c_info_type = 'COLLECTION_LOGIN'".format(
                coll_id,
                img_ext,
                res_idx - 1
            )
            self.curs.execute(sql)
            self.conn.commit()
        return True

    def coll_res_list(self, coll_id, cate_list):
        """
        查询藏品所有的资源信息
        :param coll_id: 藏品ID
        :return: 成功返回dict集合,失败返回 None
        """
        self.re_connect()
        with self.conn:
            sql = "SELECT * FROM `potato_resource_info` WHERE `res_del` = 0 AND `res_belong_type` = 'COLLECTION_LOGIN_INFO' AND `res_cate` in ({}) AND `res_relation_id` = {} ORDER BY `id` DESC".format(
                ','.join(list(map(lambda v: '\'{}\''.format(v), cate_list))), coll_id)
            self.curs.execute(sql)
            return self.curs.fetchall()

    def coll_all(self):
        self.re_connect()
        with self.conn:
            sql = "SELECT * FROM `kunlun_collection_login` WHERE `cl_mid` = {} AND c_info_type = 'COLLECTION_LOGIN' AND `c_del` = 0 AND `c_draft` = 0 ORDER BY `id` DESC".format(
                self.mid)
            self.curs.execute(sql)
            return self.curs.fetchall()

    def add_resource(self, res=None):
        """
        插入资源信息记录
        :param res: 资源信息
        :return: 插入记录
        """
        if res is None:
            res = {
                'relationId': 0,
                'ext': '',
                'belongType': 'COLLECTION_LOGIN_INFO',
                'cate': 'IMAGE',
                'name': '未命名',
                'description': '描述',
                'key': 'http://domain.com/example.jpg',
                'size': 0,
                'contentType': 'image/png',
                'suffix': 'jpg',
                'cover': 'http://domain.com/example.jpg',
                'source': '',
                'width': 0,
                'height': 0,
                'ip': '127.0.0.1',
                'partCount': 1,
                'savePath': '',
                'md5': ''
            }
        self.re_connect()
        with self.conn:
            sql = "INSERT INTO `potato_resource_info`(`res_num`, `m_id`, `res_belong_type`, `res_relation_id`, `res_cate`, " \
                  "`res_name`, `res_description`, `res_key`, `res_size`, `res_content_type`, `res_suffix`, `res_add_user`, " \
                  "`res_add_time`, `res_update_user`, `res_update_time`, `res_cover`, `res_source`, `res_status`, `res_reason`, " \
                  "`res_width`, `res_height`, `res_ext`, `res_config`, `res_ip`, `res_part_count`, `res_del`, `res_save_path`, " \
                  "`res_md5`) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'SUCCESS', %s, %s, %s, " \
                  "%s, %s, %s, %s, 0, %s, %s);"
            self.curs.execute(sql, (
                util.rand_code(32).lower(), self.mid, res.get('belongType'), res.get('relationId'), res.get('cate'),
                res.get('name'),
                res.get('description'), res.get('key'),
                res.get('size'), res.get('contentType'), res.get('suffix'), self.uid, util.now_ts_s(), self.uid,
                util.now_ts_s(),
                res.get('cover'),
                res.get('source'), '', res.get('width'), res.get('height'), res.get('ext'), '', res.get('ip'),
                res.get('partCount'), res.get('savePath'), res.get('md5')))
            self.conn.commit()
        return True

    def latest_resource_data(self, count=100):
        """
        打印最新资源信息
        :param count: 获取数量
        :return:
        """
        self.re_connect()
        with self.conn:
            sql = "SELECT `id`, `res_num`, `res_name`, `res_key` FROM `potato_resource_info` ORDER BY `id` DESC limit 0, %s"
            self.curs.execute(sql, count)
            return self.curs.fetchall()

    def all_museum(self):
        """
        所有博物馆信息
        """
        self.re_connect()
        with self.conn:
            sql = "select id, `m_num` num, `m_name` `name` from kunlun_museum"
            self.curs.execute(sql)
            return self.curs.fetchall()

    def museum_one(self, mid):
        """
        博物馆信息
        """
        self.re_connect()
        with self.conn:
            sql = "select id, `m_num` num, `m_name` `name` from kunlun_museum where id = {}".format(mid)
            self.curs.execute(sql)
            return self.curs.fetchone()

    def all_user(self):
        """
        打印所有用户信息
        """
        self.re_connect()
        with self.conn:
            sql = "SELECT u.id,u_real_name real_name,m.id mid,m.m_name mname,u_phone phone,u_email email FROM " \
                  "potato_user u LEFT JOIN kunlun_museum m ON u.m_id AND m.id WHERE u.u_del = 0"
            self.curs.execute(sql)
            return self.curs.fetchall()

    def user_one(self, uid):
        """
        查询用户信息
        """
        self.re_connect()
        with self.conn:
            sql = "SELECT u.id,u_real_name real_name,m.id mid,m.m_name mname,u_phone phone,u_email email FROM " \
                  "potato_user u INNER JOIN kunlun_museum m ON u.m_id AND m.id WHERE u.id = {}".format(
                uid)
            self.curs.execute(sql)
            return self.curs.fetchone()

    def resource_one_by_md5(self, md5):
        """
        根据MD5查询博物馆资源信息
        """
        self.re_connect()
        with self.conn:
            sql = "SELECT * FROM `potato_resource_info` WHERE m_id = {} AND res_md5 = '{}' AND res_del = 0 ORDER BY `id` DESC".format(
                self.mid, md5)
            self.curs.execute(sql)
            return self.curs.fetchone()

    def museum_resource_stat(self, mid):
        """
        博物馆资源统计
        """
        self.re_connect()
        with self.conn:
            sql = "SELECT res_cate cate,count(res_cate) count, CASE " \
                  "WHEN ABS(sum(res_size)) < 1024 THEN CONCAT( ROUND( sum(res_size), 2 ), ' Bytes') " \
                  "WHEN ABS(sum(res_size)) < 1048576 THEN CONCAT( ROUND( (sum(res_size)/1024), 2 ), ' KB') " \
                  "WHEN ABS(sum(res_size)) < 1073741824 THEN CONCAT( ROUND( (sum(res_size)/1048576), 2 ), ' MB') " \
                  "WHEN ABS(sum(res_size)) < 1099511627776 THEN CONCAT( ROUND( (sum(res_size)/1073741824), 2 ), ' GB' ) " \
                  "WHEN ABS(sum(res_size)) < 1125899906842624 THEN CONCAT( ROUND( (sum(res_size)/1099511627776), 2 ), ' TB') " \
                  "WHEN ABS(sum(res_size)) < 1152921504606846976 THEN CONCAT( ROUND( (sum(res_size)/1125899906842624), 2 ), ' PB' ) " \
                  "WHEN ABS(sum(res_size)) < 1180591620717411303424 THEN CONCAT( ROUND( (sum(res_size)/1152921504606846976) ,2), ' EB' ) " \
                  "WHEN ABS(sum(res_size)) < 1208925819614629174706176 THEN CONCAT( ROUND( (sum(res_size)/1180591620717411303424), 2), ' ZB' ) " \
                  "WHEN ABS(sum(res_size)) < 1237940039285380274899124224 THEN CONCAT( ROUND( (sum(res_size)/1208925819614629174706176), 2), ' YB' ) " \
                  "WHEN ABS(sum(res_size)) < 1267650600228229401496703205376 THEN CONCAT( ROUND( (sum(res_size)/1237940039285380274899124224), 2), ' BB' ) " \
                  "END size FROM `potato_resource_info`" \
                  " WHERE res_del=0 AND res_belong_type='COLLECTION_LOGIN_INFO' AND m_id = {} AND res_relation_id in (select " \
                  "id from kunlun_collection_login where c_del = 0 and c_draft = 0) GROUP BY res_cate".format(
                mid)
            self.curs.execute(sql)
            return self.curs.fetchall()

    def museum_coll_count(self, mid):
        """
        博物馆藏品数量
        """
        self.re_connect()
        with self.conn:
            sql = "SELECT count(id) count FROM `kunlun_collection_login` WHERE cl_mid = {} AND c_del = 0 and c_draft = 0".format(
                mid)
            self.curs.execute(sql)
            return self.curs.fetchone()['count']

    def del_fail_resource(self):
        """
        删除失败的资源记录
        :return: 数量
        """
        self.re_connect()
        with self.conn:
            sql = "update potato_resource_info set res_del = 1 where res_status = 'FAIL' and res_del = 0;"
            self.curs.execute(sql)
            self.conn.commit()
            return self.curs.rowcount
        return 0
