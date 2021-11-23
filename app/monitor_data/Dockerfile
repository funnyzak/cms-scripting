FROM rackspacedot/python37
COPY . /app
WORKDIR /app

# Install Virtualenv:
RUN pip3 install virtualenv -i https://pypi.tuna.tsinghua.edu.cn/simple

# Enable Virtualenv:
RUN virtualenv venv
RUN . venv/bin/activate

# Install dependencies:
RUN pip3 install -r ./requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# set PATH
ENV VIRTUAL_ENV=/app/venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
ENV TZ=Asia/Shanghai

CMD ["python3", "main.py"]
