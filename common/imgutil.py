#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
   created     ： The May 21 10:22 AM 2021
   filename    ： imgutil.py
   author      :  Leon
   email       :  silenceace@gmail.com
   Description :
"""
__author__ = 'Leon'

import os
from common import util
import exifread
from PIL import Image, ImageFile
ImageFile.LOAD_TRUNCATED_IMAGES = True

def open_image(image_file):
    # 打开图片
    if os.name == "nt":
        os.system('start ' + image_file)  # for Windows
    else:
        if os.uname()[0] == "Linux":
            if "deepin" in os.uname()[2]:
                os.system("deepin-image-viewer " + image_file)  # for deepin
            else:
                os.system("eog " + image_file)  # for Linux
        else:
            os.system("open " + image_file)  # for Mac

def save_image(resp, image_file):
    # 保存图片
    with open(image_file, 'wb') as f:
        for chunk in resp.iter_content(chunk_size=1024):
            f.write(chunk)

def img_size(file_path):
    if not is_img(file_path) or not os.path.exists(file_path):
        return None
    try:
        img = Image.open(file_path)
        return dict(width=img.width, height=img.height)
    except Exception:
        return None

def img_compress(img_path, img_save_path, scale_percent=None, scale_quality=None):
    """
    压缩图片
    :param img_path: 原始图片路径
    :param img_save_path: 压缩后图片的保存路径
    :param scale_percent: 压缩图片比0-100
    :return: 如果压缩成功则返回True 否则返回False
    """
    try:
        if not is_img(img_path):
            return False
        if scale_percent is None:
            scale_percent = 30
        if scale_quality is None:
            scale_quality = 85

        scale_val = round(scale_percent / 100.0, 2)

        img = Image.open(img_path)
        w, h = round(img.width * scale_val), round(img.height * scale_val)  # 去掉浮点，防报错
        img = img.resize((w, h), Image.ANTIALIAS)
        img.save(img_save_path, optimize=True, quality=scale_quality)  # 质量为85效果最好
        return True
    except Exception:
        return False

def img_exif(path, exclude_start_withs=None):
    """
    获取图片Exif信息
    :param path: 图录路径
    :param exclude_start_withs: 排除的符合条件的前缀列表
    :return:
    """
    if exclude_start_withs is None:
        exclude_start_withs = ['MakerNote ', 'EXIF MakerNote', 'EXIF UserComment',
                               'Thumbnail JPEGInterchange', 'GPS GPSVersionID', 'EXIF ExifVersion',
                               'EXIF ComponentsConfigura']

    if not is_img(path) or not os.path.exists(path):
        return None
    try:
        f = open(path, 'rb')
        tags = exifread.process_file(f)

        def not_start_with_filter(key):
            for _sw in exclude_start_withs:
                if key.startswith(_sw):
                    return False
            return True

        exif_info = dict()
        for tag in filter(not_start_with_filter, tags.keys()):
            if tag not in ('JPEGThumbnail', 'TIFFThumbnail'):
                val = tags[tag].values if tags[tag].values is None or type(tags[tag].values) == str \
                    else (
                    ','.join(list(map(lambda x: str(x), tags[tag].values))) if len(tags[tag].values) > 1
                    else ''.join(list(map(lambda x: str(x), tags[tag].values)))
                )
                if val == '' or not val:
                    continue
                exif_info[tag] = val
        return exif_info
    except Exception:
        return None

def is_photo(url):
    return util.url_with_ext(url, 'jpg,jpeg,png,bmp,gif,cr2,tif,tiff')

def is_img(url):
    return util.url_with_ext(url, 'jpg,jpeg,png,bmp,gif')

def img_exif(path, exclude_start_withs=None):
    """
    获取图片Exif信息
    :param path: 图录路径
    :param exclude_start_withs: 排除的符合条件的前缀列表
    :return:
    """
    if exclude_start_withs is None:
        exclude_start_withs = ['MakerNote ', 'EXIF MakerNote', 'EXIF UserComment',
                               'Thumbnail JPEGInterchange', 'GPS GPSVersionID', 'EXIF ExifVersion',
                               'EXIF ComponentsConfigura']

    if not is_img(path) or not os.path.exists(path):
        return None
    try:
        f = open(path, 'rb')
        tags = exifread.process_file(f)

        def not_start_with_filter(key):
            for _sw in exclude_start_withs:
                if key.startswith(_sw):
                    return False
            return True

        exif_info = dict()
        for tag in filter(not_start_with_filter, tags.keys()):
            if tag not in ('JPEGThumbnail', 'TIFFThumbnail'):
                val = tags[tag].values if tags[tag].values is None or type(tags[tag].values) == str \
                    else (
                    ','.join(list(map(lambda x: str(x), tags[tag].values))) if len(tags[tag].values) > 1
                    else ''.join(list(map(lambda x: str(x), tags[tag].values)))
                )
                if val == '' or not val:
                    continue
                exif_info[tag] = val
        return exif_info
    except Exception:
        return None

