# Dockerized BASE for RUM - INGV Rule Manager Light
# Based on ubuntu:20.04
#
# Description:
# BASE CLIENTS: MONGO & OBSPY + PYHANDLE used for  Rule Manager execution procedure, in python 3
#
# imageName:'base-ruler:1.7'
#
# build:
# build command: sudo docker build -t "base-ruler:1.7" .
#
# Use docker-compose yaml

FROM       ubuntu:20.04
MAINTAINER massimo.fares@ingv.it

SHELL ["/bin/bash", "-c"]

# Add a non-root user to prevent files being created with root permissions on host machine.
# put  ID equals to host
ARG PUID=1000
ARG PGID=1000
ARG USER=sysop
 
# user
RUN groupadd -g ${PGID} ${USER} && \
    useradd -u ${PUID} -g ${USER} --home-dir /home/${USER} ${USER} && \
    mkdir -p /home/${USER} && \
    chown -R ${USER}:${USER} /home/${USER} && \
    chsh ${USER} -s /bin/bash

RUN apt-get update
RUN DEBIAN_FRONTEND=noninteractive apt-get install -y apt-transport-https
RUN apt-get update --fix-missing

# install dependencies
RUN DEBIAN_FRONTEND=noninteractive apt-get install -y    rsync wget git vim python3-dev python3-pycurl python3-simplejson
RUN DEBIAN_FRONTEND=noninteractive apt-get install -y    libcurl4-gnutls-dev libssl-dev pkg-config  iputils-ping
RUN DEBIAN_FRONTEND=noninteractive apt-get install -y    python3 python3-psutil python3-requests python3-jsonschema libfuse2
RUN DEBIAN_FRONTEND=noninteractive apt-get install -y    python3-setuptools  build-essential python3-pip
RUN DEBIAN_FRONTEND=noninteractive apt-get install -y    libxml2-dev libxslt1-dev libz-dev libfreetype6-dev 
RUN DEBIAN_FRONTEND=noninteractive apt-get install -y    python3-numpy python3-scipy python3-matplotlib sudo
RUN DEBIAN_FRONTEND=noninteractive apt-get install -y    procps less nano vim git exim4 mutt gcc gcc-multilib make
RUN DEBIAN_FRONTEND=noninteractive apt-get install -y    libtool build-essential mysql-client rsync wget net-tools telnet dnsutils libxml2-utils
RUN echo  "deb http://deb.obspy.org bionic main" >> /etc/apt/sources.list
RUN wget --quiet -O - https://raw.githubusercontent.com/obspy/obspy/master/misc/debian/public.key | sudo apt-key add -

RUN apt-get update

# obspy
RUN pip3 install obspy

# mongo driver
RUN pip3 install pymongo

# eudat pyhandle
RUN pip3 install pyhandle

# RUM dependencies
RUN pip3 install pyinotify importlib mysql-connector-python
RUN pip3 install pyyaml
RUN pip3 install validators


#make RUM app dir
RUN mkdir -p /usr/src/code

# volumes
RUN mkdir -p /usr/src/code/log
RUN mkdir -p /usr/src/code/project
RUN mkdir -p /var/lib/rum_area/incoming

# permission
RUN   chown -R ${USER}:${USER} /var/lib && \
      chown -R ${USER}:${USER} /usr/src/code/

# set user
USER ${USER}

# BASHRC
COPY --chown=${USER}:${USER} ./bashrc /home/${USER}/.bashrc
RUN echo "source /home/${USER}/.profile" >> /home/${USER}/.bashrc
RUN echo "PS1='${debian_chroot:+($debian_chroot)}\u@\h(docker):\w\$ '" >> /home/${USER}/.bashrc
RUN source /home/${USER}/.bashrc

# Working Directory
WORKDIR /usr/src/code

# with yaml docker-compose = tty: true
# the follow line don't care anymore
# ENTRYPOINT ["tail", "-f", "/dev/null"]

