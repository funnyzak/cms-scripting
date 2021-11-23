FROM funnyzak/java8-nodejs-python-go-etc
COPY . /app
WORKDIR /app

# Install dependencies:
RUN pip3 install -r ./requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

ENV TZ=Asia/Shanghai

CMD ["python3", "main.py"]
