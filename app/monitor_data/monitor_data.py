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

class RandomMonitorDataServer(object):
    def __init__(self, config):
        self.config = config

    # 生存随机设备随机日志信息
    def random_brt_device_data(self, device, time_seed=10):
        log = {
            "ble_addr": device['id'],
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
        _device_list = []
        for device in gateway['deviceList']:
            _device_list.append(self.random_brt_device_data(
                device, gateway['postInterval']))
        # 生成设备日志结束

        return json.dumps({
            "devices": _device_list,
            "seq_no": rd.randrange(0, 10, 1),
            "cbid": gateway['gatewayId'],
            "time": int(time.time()),
            "cmd": rd.randrange(0, 1000, 1),
        }, sort_keys=True, indent=4)

    # 恒湿机数据

    def random_cthm_device_data(self, device, post_interval):
        pass

    # 根据单个网关配置生产一次性网关日志信息
    def random_one_gateway_json_data(self, gateway):
        if gateway['type'] == 'brt':
            return self.random_brt_gateway_data(gateway)
        elif gateway['type'] == 'cthm':
            return self.random_cthm_device_data(gateway)

    # 网关日志提交到服务器
    def post_data_to_host(self, data, post_url):
        print('post data to :', post_url, ' Data:', data)
        try:
            requests.post(post_url, data=data, headers={
                          "Content-Type": "application/json"})
        except ConnectionError:
            print('请求发送失败了。')
        except:
            print("请求发送未知异常。")
        else:
            print('成功发送请求')
        finally:
            print('POST数据执行完毕')

    # 根据网关配置发送单次数据
    def post_one_data_tohost(self):
        for gateway in self.config['list']:
            self.post_data_to_host(self.random_one_gateway_json_data(
                gateway=gateway), self.config['postUrl'][gateway['type']])

    # 根据网关配置发送单次数据
    def post_one_data_tohost_by_index(self, gateway_index=0):
        gateway = self.config['list'][gateway_index]
        self.post_data_to_host(self.random_one_gateway_json_data(gateway),
                               self.config['postUrl'][gateway['type']])

    def start(self):
        _gateway_idx = 0
        for gateway in self.config['list']:
            schedule.every(gateway['postInterval']).to(gateway['postInterval'] + 10).seconds.do(
                self.post_one_data_tohost_by_index, _gateway_idx)
            _gateway_idx += 1
        while True:
            schedule.run_pending()
            time.sleep(1)


if __name__ == '__main__':
    config_json_path = os.path.join(os.getcwd(), 'config.json')

    json_config = json.loads(
        open(config_json_path, mode='r', encoding='utf-8').read())

    _rmds = RandomMonitorDataServer(json_config)
    _rmds.start()
