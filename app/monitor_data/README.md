# Monitor Data

环境监测模型数据模拟发送。通过 POST 发送。使用 Pyhton37。

支持多个发送任务、目标同时运行。

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

## 后台运行

使用Compose使用Docker创建容器运行。

创建如下 `docker-compose.yml` 文件:

```yaml
# 注意修改对应的配置文件
version: '3'
services:
  app:
    build:
      context: .
      dockerfile: ./Dockerfile
    container_name: monitor_data
    restart: always
    command: ['python3', 'main.py', 'config.json']
    volumes:
      - .:/app

```

然后 `docker-composeu up -d` 启动。
