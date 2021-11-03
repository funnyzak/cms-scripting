#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
   created     ： The Jan 26 6:28 PM 2021
   filename    ： exception.py
   author      :  Leon
   email       :  silenceace@gmail.com
   Description :
"""
__author__ = 'Leon'


class PException(Exception):
    def __init__(self, message):
        super().__init__(message)
