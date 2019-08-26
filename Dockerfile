FROM ubuntu:bionic

ENV DEBIAN_FRONTEND noninteractive

WORKDIR /opt/pdos/

# Setup Ubuntu
RUN apt-get -qq update --yes
RUN apt-get -qq install wget python3 python3-setuptools python3-pip --yes

ADD . /opt/pdos
RUN python3 setup.py install
RUN python3 solidity/install_solc.py install
