# coding: utf-8

"""
file:monitor_data.py
date:2019-08-06
update:2021-11-23
author:leon
desc: 发送随机设备监测数据到服务器
"""

import random as rd
import json
import time
import requests
import schedule
import json
import os
import shutil
import sys
import logging
import logging.handlers


EXEC_PATH = os.path.dirname(os.path.abspath(__file__))
LOG_PATH = os.path.join(EXEC_PATH, 'logs')
if not os.path.exists(LOG_PATH):
    os.makedirs(LOG_PATH)


def new_logger(log_name=None):
    if log_name is None:
        log_name = 'info.log'

    logger = logging.getLogger(os.path.splitext(log_name)[0])
    LOG_FILENAME = os.path.join(LOG_PATH, log_name)
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(process)d-%(threadName)s - '
                                  '%(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s')
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    logger.addHandler(console_handler)
    file_handler = logging.handlers.RotatingFileHandler(
        LOG_FILENAME, maxBytes=5242880, backupCount=5, encoding="utf-8")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    return logger


logger = new_logger()


_TML_CONFIG_JSON_PATH = os.path.join(os.getcwd(), 'config.sample.json')


class RandomMonitorData(object):
    def __init__(self, config):
        self.config = config

    # 生存随机设备随机日志信息
    def random_brt_device_data(self, device, time_seed=10):
        """
        :param device: 设备对象
        """
        log = {
            "ble_addr": device['mac'],
            "addr_type": 1,
            "scan_rssi": rd.randrange(50, 90, 1),
            "scan_time": int(time.time()) - rd.randrange(0, time_seed, 1),
            "humi": str(format(device['humi'] - rd.randrange(0, 5, 1), "x")),
            "pwr_percent": str(format(device['pwr'], "x")),
            "temp": str(format(device['temp'] - rd.randrange(0, 3, 1), "x"))
        }
        if device['type'] == 'VOC':
            log['lux'] = str(
                format(device['lux'] - rd.randrange(0, 5, 1), "x"))
            log['tvoc'] = str(
                format(device['tvoc'] - rd.randrange(0, 5, 1), "x"))
            log['eco2'] = str(
                format(device['eco2'] - rd.randrange(0, 5, 1), "x"))
        return log

    def random_brt_gateway_data(self, gateway):
        """
        : 生成brt网关数据
        :param gateway: 网关信息
        """
        _device_list = []
        for device in gateway['deviceList']:
            _device_list.append(self.random_brt_device_data(
                device, gateway['timeSeed']))

        return json.dumps({
            "devices": _device_list,
            "seq_no": rd.randrange(0, 10, 1),
            "cbid": gateway['id'],
            "time": int(time.time()),
            "cmd": rd.randrange(0, 1000, 1),
        }, sort_keys=True, indent=4)

    def random_cthm_gateway_device_data(self, gateway):
        """
        : 生成恒湿机网关数据
        """
        device = gateway['device']
        log = {
            "macId": device['mac'],
            "localIp": device['ip'],
            "time": int(time.time()) - rd.randrange(0, gateway['timeSeed'], 1),
            "humi": str(format(device['humi'] - rd.randrange(0, 100, 10), "x")),
            "temp": str(format(device['temp'] - rd.randrange(0, 150, 10), "x")),
            "runningStatus": device['runningStatus']
        }
        return json.dumps(log, sort_keys=True, indent=4)

    def random_one_gateway_json_data(self, gateway):
        """
        : 根据单个网关配置生产一次性网关日志信息
        """
        if gateway['type'] == 'brt':
            return self.random_brt_gateway_data(gateway)
        elif gateway['type'] == 'cthm':
            return self.random_cthm_gateway_device_data(gateway)

    def post_data_to_host(self, data, post_url):
        """
        : 网关日志提交到服务器
        """
        logger.info('Post Data: %s To %s .', data, post_url)
        try:
            requests.post(post_url, data=data, headers={
                          "Content-Type": "application/json"})
        except ConnectionError:
            logger.error('post connect error.')
        except:
            logger.error("post throw error.")
        else:
            logger.info('post success.')
        finally:
            logger.info('post done.')

    def post_one_data_tohost(self):
        """
        : 根据网关配置发送单次数据
        """
        for gateway in self.config['list']:
            self.post_data_to_host(self.random_one_gateway_json_data(
                gateway=gateway), self.config['postUrl'][gateway['type']])

    def post_one_data_tohost_by_index(self, gateway_index=0):
        """
        : 根据网关配置发送单次数据
        """
        gateway = self.config['list'][gateway_index]
        self.post_data_to_host(self.random_one_gateway_json_data(gateway),
                               self.config['postUrl'][gateway['type']])

    def start(self):
        _gateway_idx = 0
        for gateway in self.config['list']:
            schedule.every(gateway['interval']).to(gateway['interval'] + 10).seconds.do(
                self.post_one_data_tohost_by_index, _gateway_idx)
            _gateway_idx += 1
            logger.info('gateway: %s already schedule.', gateway['id'])
        logger.info('has %s gateway started.', len(self.config['list']))
        while True:
            schedule.run_pending()
            time.sleep(1)


if __name__ == '__main__':
    arg_path = sys.argv[1] if len(sys.argv) > 1 else ''
    config_json_path = arg_path if arg_path is not None and len(arg_path) > 0 else os.path.join(
        os.getcwd(), 'config.json')

    # 如果配置文件不存在则创建示例文件
    if not os.path.exists(config_json_path):
        shutil.copy(_TML_CONFIG_JSON_PATH, config_json_path)

    json_config = json.loads(
        open(config_json_path, mode='r', encoding='utf-8').read())

    _rmds = RandomMonitorData(json_config)
    _rmds.start()
