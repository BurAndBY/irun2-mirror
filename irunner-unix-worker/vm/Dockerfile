FROM ubuntu:bionic

RUN apt-get update && apt-get install -y \
    python3-pip \
    sudo \
    psmisc \
    gawk \
    bc

RUN pip3 install \
    pytest==5.4.2 \
    pytest-timeout==1.3.4

RUN groupadd --gid 999 bsu && \
    useradd --uid 999 --gid bsu --create-home --shell /bin/bash student && \
    usermod -a -G sudo student && \
    echo '%sudo ALL=(ALL) NOPASSWD:ALL' >> /etc/sudoers

RUN mkdir --parents /opt/irunner/src && \
    mkdir --parents /opt/irunner/dst && \
    chown -R student:bsu /opt/irunner/dst

USER student

WORKDIR /home/student

ENV LANG C.UTF-8
ENV LC_ALL C.UTF-8
