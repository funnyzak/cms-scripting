import os
import shutil

'''
    该脚本用于复制提取目录文件
    @author hch
    @date   2022-04-25
    @version 2.0
    @historyVersion 1.0 leo
'''
def exists(path:str) :
    '''
        判断当前路径是否存在
        @param path 路径
        @return Ture 或 False
    '''
    checkFlag = os.path.exists(path)
    if not checkFlag : 
        print("路径：%s 不存在"%path)
    return checkFlag

def isDir(path:str) :
    '''
        判断是否为是目录
        @param path 路径
        @return True 或 False
    '''
    return os.path.isdir(path)

def getAllFileOrDir(path:str, roles) :
    '''
        获取当前路径下所有的符合规则的目录名
        @param path 当前路径
        @param roles 规则
        @return 符合规则的目录名
    '''
    list = []
    files = os.listdir(path)
    for file in files :
        # 得到该文件下所有目录的路径
        subPath = os.path.join(path, file)
        if roles(subPath) :
            list.append(os.path.split(subPath)[1])
    
    return list

def searchFiles(root:str, ext:str, list) :
    '''
        搜索目录指定文件
        @param path 目录路径
        @param ext  文件后缀名
        @return 符合后缀名的文件
    '''
    items = os.listdir(root)
    for item in items:
        path = os.path.join(root, item)
        if os.path.isdir(path):
            searchFiles(path, ext, list)
        elif os.path.splitext(item)[1] == ext:
            list.append(path)
    return list

def distNameExecRole(parentDir:str, distName:str) :
    '''
        根据父目录生成子目录规则
        @param parentDir 父目录名称
        @param distName 子目录名变量
        @return 父目录与子目录的结合
    '''
    return parentDir + "_" + distName


def multCopy(currentPath:str, dirList, subName:str, distName:str, fileExt:str, copyStartIndex:int, copyEndIndex:int, copyStep:int, distNameExecRole) :
    '''
        复制文件
        @param currentPath     当前脚本所在目录
        @param dirList         脚本文件的所有同级目录
        @param subName         要copy的文物子目录,例如：成果照片
        @param distName        要生成到的文物子目录名,例如：封面照片
        @param fileExt         要copy的文物文件的后缀名，例如：.jpg
        @param copyStartIndex  将要copy的文件索引开始数
        @param copyEndIndex    将要copy的文件索引结束数
        @param copyStep        将要copy的步长
        @param distNameExecRole生成子目录规则
    '''
    for index in range(len(dirList)) :
        print('\n\n 正在处理第 %s 个目录：%s'%(index + 1, os.path.join(currentPath, dirList[index])))
        # 要复制的目标文件夹
        targetDir = os.path.join(currentPath, dirList[index], distNameExecRole(dirList[index],distName))
        # 要查找的源文件夹
        sourceDir = os.path.join(currentPath, dirList[index], subName)

        # 如果源文件路径不存在，则跳过本次循环
        if not exists(sourceDir) :
            continue

        # 搜索指定后缀名的文件
        extFiles = searchFiles(sourceDir, fileExt, [])
        if len(extFiles) == 0 : 
            print("\n没有找到匹配的文件。")
            continue

        # 如果要复制的目标文件夹不存在则创建
        if not exists(targetDir) :
            print('正在创建 %s 目录'%targetDir)
            os.makedirs(targetDir)

        # 浅复制 将符合后缀的文件 复制给变量willCopyFiles
        willCopyFiles = extFiles.copy()
        if len(willCopyFiles) == 0 :
            continue
        # 根据设置的复制的开始位置、结束位置、步长进行切片
        copyEndIndex = copyEndIndex if copyEndIndex <= len(willCopyFiles) else len(willCopyFiles)
        willCopyFiles = willCopyFiles[copyStartIndex - 1 : copyEndIndex : copyStep + 1]
        
        for index in range(len(willCopyFiles)) :
            # 复制到目标文件的全路径名
            distFileName = os.path.join(targetDir, os.path.basename(willCopyFiles[index]).replace(fileExt, '') + fileExt)
            print('将 %s 复制到 %s'%(willCopyFiles[index], distFileName))
            shutil.copyfile(willCopyFiles[index], distFileName)

if __name__ == '__main__' :
    # 当前脚本所在目录路径
    currentPath = os.getcwd() 
    # 要copy的文物下的哪一个文件夹
    subName = '成果照片'
    # 要copy的文物资源后缀名
    fileExt = '.jpg'
    # 要生成的文物下的目录名称
    distName = '提取照片'
    # 复制开始的索引，比如从文物下的'成果照片'下的第一个开始复制，包含第一个 
    starCopyIndex = 1
    # 复制结束的索引，比如到文物下的'成果照片'下的到第二个结束，包含第二个
    endCopyIndex = 1
    # 复制的步长，比如每隔一个复制或每隔两个复制，0则为依次复制
    copyStep = 0

    dirList = getAllFileOrDir(currentPath, isDir) # 脚本文件的所有同级目录
    multCopy(currentPath, dirList, subName, distName, fileExt, starCopyIndex, endCopyIndex, copyStep, distNameExecRole)