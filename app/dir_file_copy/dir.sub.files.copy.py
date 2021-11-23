# coding: utf-8

"""
file:kl.copy.py
date:2019-06-18
update: 2019-09-12
author:leon
desc: 遍历目录 /a 下所有的子目录，把 /a/xx 下的指定目录的指定文件按规则复制到 xx 同级的目录
"""

import shutil
import os, shutil


# path 处理的根目录
# subName 要copy的文物子目录
# distName 要复制到的同级目录名称($parent代表上级目录名称变量)
# copyMaxCount复制最大数量 stepCopy是否步长复制、否则按顺序负责
# fileExt要copy的文件类型  eg:.jpg
# renamePrefix文件重命名前缀（$origin原文件名, %loop顺序序号）

def multCopy(path, subName, fileExt, distName, renamePrefix, copyMaxCount, stepCopy=True):
    if (os.path.exists(path)):
        # 获取该目录下的所有文件或文件夹目录
        files = os.listdir(path)
        list = []  # 声明list
        for file in files:
            # 得到该文件下所有目录的路径
            m = os.path.join(path, file)
            # 判断该路径下是否是文件夹
            if (os.path.isdir(m)):
                h = os.path.split(m)
                list.append(h[1])

        loop = 1
        for fn in list:
            print('\n\n' + str(loop) + '.当前处理目录：' + os.path.join(path, fn))
            # 要复制的目标文件夹 #
            distDir = os.path.join(path, fn, distName.replace('$parent', fn))
            # 查找的源文件夹 #
            soureDir = os.path.join(path, fn, subName)

            # 如果源文件夹不存在则跳过
            if bool(1 - os.path.exists(soureDir)):
                print('\n没有找到匹配目录。')
                continue

            # 搜索指定后缀的文件 #
            extFiles = searchFiles(soureDir, fileExt, [])

            if len(extFiles) == 0:
                print('\n没有找到匹配的文件。')
                continue;

            # 如果不存在则创建目录目录
            if not os.path.exists(distDir):
                os.makedirs(distDir)

            # 计算可复制的数量
            willCopyCount = copyMaxCount if len(extFiles) > copyMaxCount else len(extFiles)
            print('\n 共找到 %s 文件：%s 个。 将复制 %s 个到目标目录。' % (fileExt, len(extFiles), willCopyCount))

            # 处理最终复制的文件列表
            willCopyFiles = extFiles.copy()

            if len(extFiles) > willCopyCount:
                loop = 0
                copyedCount = 0
                willCopyFiles = []

                for ef in extFiles:
                    if (copyedCount == willCopyCount): break

                    loop += 1
                    if (stepCopy == False):
                        willCopyFiles.append(ef)
                        copyedCount += 1
                    elif ((loop - 1) % int(len(extFiles) / willCopyCount) == 0):
                        willCopyFiles.append(ef)
                        copyedCount += 1

            loop2 = 1
            for ef in willCopyFiles:
                distFileName = os.path.join(distDir,
                                            renamePrefix.replace('$origin', os.path.basename(ef).replace(fileExt, ''))
                                            .replace('$loop', str(loop2)).replace('$ext', fileExt))
                print(ef, distFileName)
                shutil.copyfile(ef, distFileName)
                loop2 += 1
        loop += 1


# 搜索目录指定文件
def searchFiles(root, ext, list):
    items = os.listdir(root)
    for item in items:
        path = os.path.join(root, item)
        if os.path.isdir(path):
            searchFiles(path, ext, list)
        elif os.path.splitext(item)[1] == ext:
            list.append(path)
    return list


if __name__ == '__main__':
    curPath = os.getcwd()
    print('当前目录：' + curPath)
    # multCopy(curPath, '采集模型', '.obj', '成果模型', '成果', 5)
    multCopy(curPath, '采集照片', '.jpg', '$parent_询价参考', '$loop.$origin$ext', 5)
