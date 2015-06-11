FROM ubuntu:14.04

# Configure apt

RUN echo 'deb http://us.archive.ubuntu.com/ubuntu/ precise universe' >> /etc/apt/sources.list
RUN apt-get -y update

RUN apt-get install -y build-essential git curl
RUN apt-get install -y python python-dev python-setuptools
RUN apt-get install -y software-properties-common python-software-properties
RUN apt-get install -y libpq-dev libffi-dev libxml2-dev libxslt1-dev 
RUN apt-get install -y pandoc
RUN easy_install pip

RUN apt-get -y update

# install our code
ADD . /code/hasjob

# run pip install
RUN pip install -r /code/hasjob/requirements.txt

EXPOSE 5000
EXPOSE 5432