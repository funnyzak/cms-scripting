# CollScriptingScanResource

## 主要功能

针对藏品资源管理系统的各种业务下的数据处理脚本程序。

## 运行环境

- [Python 3](https://www.python.org/)

## 第三方库

- 需要使用到的库已经放在requirements.txt，使用pip安装的可以使用指令  
  `pip install -r requirements.txt`
- 如果国内安装第三方库比较慢，可以使用以下指令进行源加速
  `pip install -i https://pypi.doubanio.com/simple/ -r requirements.txt`


## 配置当前目录执行环境

安装virtualenv
```bash
pip install -i https://pypi.doubanio.com/simple/ virtualenv
```

在程序目录执行
```bash
virtualenv venv
source venv/bin/activate
```
然后执行如上命令

## 使用教程

1. 下载Python3安装包，安装和配置环境
2. 复制一份 config.sample.ini 为 config.ini
3. 复制一份 config.sample.json 为 config.json
4. 根据实际情况填写和config.ini配置信息、config.json配置信息
5. 在执行目录执行 python3 main.py

## 运行main.py

```bash
python main.py
```

根据提示选择相应功能即可。 特别说明：main.py操作选项已封装以下其他脚本功能。

## config.json说明

* coll_api_paths 为藏品系统API请求路径
* scan_config 为扫描文件夹配置，其中 ext_list 为扫描的文件类型；dir_name_list为扫描文物下级的文件夹类别，如果是多级文件夹请用/分隔。
* folder_check_config 为检查文件夹资源配置。
* get_res_num_rules 为获取单一目录下资源文件匹配规则
* resource_cate_ext_list 为配置资源类型包含的资源格式
* execl_convert 为一普表格转换列提取配置


## 脚本说明

### scan_res.py

扫描藏品资源文件夹下子业务目录，并分别扫描业务目录数据并入库资源信息。

> 使用时需配置： config.ini=> common db coll scan_res scan_res_common messenger节点、config.json=>scan_config节点

```bash
python scan_res.py
```

### folder_check.py

检查成果移交文件夹的数据整理情况，主要检查各目录是否有对应的数据资源文件。运行方式：

> 使用时需配置：config.json=>folder_check_config


```bash
python folder_check.py 
```

### folder_create.py

根据Execl表格批量创建数据移交的整理文件夹结构。运行方式。

> Execl模板表格和目录结构见: /tmp/folder_create。

```bash
python folder_create.py
```

### batch_upload_xls.py

批量导入Execl表格到藏品系统

```bash
# 参数1：1/2 导入藏品信息/导入柜架信息  参数2：要导入的表格路径
python3 batch_upload_xls.py '1' '/Users/potato/Desktop/test3'
```

### import_coll_table_covert.py

一普藏品表格转换为藏品批量导入表格
```bash
#  参数1：3 数据行开始的索引  参数2：要处理的表格文件夹路径
python3 import_coll_table_covert.py '3' '/Users/potato/Desktop/n1'
```

### import_storage_table_covert.py

表格提取库房信息转换为藏品柜架导入表格
```bash
#  参数1：3 数据行开始的索引  参数2：要处理的表格文件夹路径
python3 import_storage_table_covert.py '3' '/Users/potato/Desktop/n1'
```

### shanxi_folder_convert

把成果提交盘的所有数据，自动转换输出为山博院的数据提交格式。

```
python3 shanxi_folder_convert.py
```

### scan_one_folder_res

扫描单个文件夹下的所有资源(图片)，根据资源名称+规则配置把资源上传到系统。

> 使用时需配置 config.json=>scan_one_folder_res 节点、 config.json => resource_cate_ext_list 节点。

```bash
python3 scan_one_folder_res.py
```

### scan_folder_and_copy_to

扫描根目录所有文件夹并复制指定格式文件到输出目录。

> 使用时需配置 config.ini=>scan_folder_res_copy_to 节点。

```bash
python3 scan_folder_and_copy_to.py
```


### 生成requirements.txt

```bash
pip freeze >requirements.txt
```