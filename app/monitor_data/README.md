# Monitor Data

环境监测模型数据模拟发送。通过 POST 发送。使用 Pyhton37.

## 使用

安装 virtualenv

```bash
pip3 install -i https://pypi.doubanio.com/simple/ virtualenv
```

进入虚拟环境

```bash
virtualenv venv
source venv/bin/activate

# 依赖安装
pip3 install -i https://pypi.doubanio.com/simple/ -r requirements.txt
```

执行

```bash
# 如果不指定配置路径则使用脚本所在目录的config.json文件
python3 main.py './config.json'
```
