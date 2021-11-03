#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
   created     ： The Jan 26 6:28 PM 2021
   filename    ： logger.py
   author      :  Leon
   email       :  silenceace@gmail.com
   Description :
"""
__author__ = 'Leon'

import os
import logging
import logging.handlers

'''
日志模块
'''
EXEC_PATH = os.path.dirname(os.path.abspath(__file__))
LOG_DIR_NAME = '../logs'
LOG_PATH = os.path.join(EXEC_PATH, LOG_DIR_NAME)

if not os.path.exists(LOG_PATH):
    os.makedirs(LOG_PATH)


def new_logger(log_name=None):
    if log_name is None:
        log_name = 'scan_res.log'

    logger = logging.getLogger(os.path.splitext(log_name)[0])
    LOG_FILENAME = os.path.join(LOG_PATH, log_name)
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(process)d-%(threadName)s - '
                                  '%(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s')
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    logger.addHandler(console_handler)
    file_handler = logging.handlers.RotatingFileHandler(
        LOG_FILENAME, maxBytes=10485760, backupCount=5, encoding="utf-8")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    return logger

logger = new_logger()
