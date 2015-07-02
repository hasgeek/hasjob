FROM ubuntu:14.04

# Configure apt

RUN echo 'deb http://us.archive.ubuntu.com/ubuntu/ precise universe' >> /etc/apt/sources.list
RUN apt-get -y update

RUN apt-get install -y build-essential git curl
RUN apt-get install -y python python-dev python-setuptools
RUN apt-get install -y software-properties-common python-software-properties
RUN apt-get install -y libpq-dev libffi-dev libxml2-dev libxslt1-dev 
RUN apt-get install -y pandoc
RUN apt-get install -y nodejs
RUN easy_install-2.7 pip

# add our requirements
ADD requirements.txt /code/hasjob/requirements.txt

# run pip install
RUN pip2.7 install -r /code/hasjob/requirements.txt

RUN pip2.7 uninstall dnspython3 -y
RUN git clone https://github.com/rthalley/dnspython && cd dnspython && python setup.py install && cd .. && rm -rf dnspython

# copy over our code
ADD . /code/hasjob

EXPOSE 5000
EXPOSE 5432
