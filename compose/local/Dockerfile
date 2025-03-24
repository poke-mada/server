FROM python:3.12
ENV PYTHONUNBUFFERED 1

RUN apt-get update -y
RUN apt-get install -y gettext

RUN apt-get clean && \
    apt-get update && \
    apt-get install -y \
    curl \
    vim \
    tmux \
    build-essential \
    libjpeg-dev \
    libpq-dev \
    default-libmysqlclient-dev && \
    pip install -U pip 3to2

RUN mkdir /app
WORKDIR /app
COPY ./requirements.txt ./requirements.txt
RUN pip install -r ./requirements.txt
COPY . /app/