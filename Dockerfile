FROM ubuntu:latest

RUN apt-get update
RUN apt-get upgrade -y
RUN apt-get install -y --fix-missing build-essential libssl-dev libffi-dev python3-dev python3-pip ffmpeg

COPY requirements.txt /tmp
RUN pip3 install -r /tmp/requirements.txt

EXPOSE 8080
WORKDIR /site

CMD ["python3", "-m", "stream"]