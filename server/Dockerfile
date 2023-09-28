FROM python:alpine3.17
COPY . /app
WORKDIR /app

RUN apk add --no-cache mariadb-connector-c-dev
RUN apk update && apk add gcc musl-dev g++ python3 python3-dev mariadb-dev build-base && pip3 install mysqlclient && apk del python3-dev mariadb-dev build-base

RUN apk add netcat-openbsd
RUN pip install --upgrade pip
RUN pip install -r requirements.txt