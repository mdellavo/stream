FROM ubuntu:latest

RUN apt-get update
RUN apt-get upgrade -y
RUN apt-get install -y --fix-missing build-essential libssl-dev libffi-dev python3-dev python3-pip ffmpeg curl

COPY requirements.txt /tmp
RUN pip3 install -r /tmp/requirements.txt

RUN curl -sL https://deb.nodesource.com/setup_6.x | bash -
RUN apt-get install -y nodejs

COPY ui/package.json /tmp
RUN cd /tmp && npm install
