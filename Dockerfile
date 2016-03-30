FROM phusion/baseimage:0.9.18

# Use baseimage-docker's init system.
CMD ["/sbin/my_init"]
RUN add-apt-repository "deb http://archive.ubuntu.com/ubuntu $(lsb_release -sc) main universe"
RUN apt-get update
RUN apt-get install -y build-essential git curl python python-dev python-setuptools software-properties-common python-software-properties libpq-dev libffi-dev libxml2-dev libxslt1-dev pandoc nodejs libjpeg-dev
RUN easy_install-2.7 pip

# add our requirements
ADD requirements.txt /code/hasjob/requirements.txt

# run pip install
RUN pip2.7 install -r /code/hasjob/requirements.txt

RUN pip2.7 uninstall dnspython3 -y
RUN git clone https://github.com/rthalley/dnspython && cd dnspython && python setup.py install && cd .. && rm -rf dnspython

# copy over our code
ADD . /code/hasjob

WORKDIR /code/hasjob/

EXPOSE 5000
EXPOSE 5432