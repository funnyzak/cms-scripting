#!/bin/bash

# 前追加方法
preAppend(){
    for folder in `ls $parentFolder`
    do
        mv $parentFolder"/"$folder $parentFolder"/"$appendText$folder
        echo "$parentFolder/$folder 修改为： $parentFolder"/"$appendText$folder"
    done
}

# 后追加方法
postAppend(){
    for folder in `ls $parentFolder`
    do
        mv $parentFolder"/"$folder $parentFolder"/"$folder$appendText
        echo "$parentFolder/$folder 修改为： $parentFolder"/"$folder$appendText"
    done
}

# 替换方法
replace(){
    echo "替换方法暂未开通"
}



# 批量修改文件夹名称
echo "请输入要批量修改文件夹的父路径"
read -p "路径：" parentFolder

echo -e "请选择要批量修改的方式
0. 前追加
1. 后追加 
2. 替换"
read -p "方式选择:" selected
echo -e "请输入文件名追加内容"
read -p "追加内容：" appendText

echo -e "
要批量修改的文件夹的父路径：$parentFolder"
if [ $selected -eq 0 ]
then
    echo "选择的方式：前追加"
elif [ $selected -eq 1 ]
then
    echo "选择的方式：后追加"
elif [ $selected -eq 2 ]
then
    echo "选择的方式：替换"
fi
echo "追加内容：$appendText"
read -p "请确认以上信息是否正确(Y/N):" confirm

if [ $confirm == 'Y' -o  $confirm == 'y' ]
then
    if [ $selected -eq 0 ]
    then 
        preAppend
    elif [ $selected -eq 1 ]
    then 
        postAppend
    elif [ $selected -eq 2 ]
    then 
        replace
    else
        echo "选择批量修改方式错误，程序结束" 
    fi
fi


