FROM ubuntu:latest

RUN apt-get update
RUN apt-get upgrade -y
RUN apt-get install -y build-essential libssl-dev libffi-dev python3-dev python3-pip

COPY requirements.txt /tmp

RUN pip3 install -r /tmp/requirements.txt
