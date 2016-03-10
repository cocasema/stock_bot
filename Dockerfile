FROM phusion/baseimage
MAINTAINER cocasema <github@cocasema.com>

# Set the locale
RUN locale-gen en_US.UTF-8
ENV LANG en_US.UTF-8
ENV LANGUAGE en_US:en
ENV LC_ALL en_US.UTF-8

RUN apt-get update
RUN DEBIAN_FRONTEND=noninteractive \
 && apt-get install -y --force-yes -q --no-install-recommends \
    python3 python3-pip \
 && apt-get autoremove -y \
 && apt-get clean autoclean \
 && rm -rf /var/lib/{apt,dpkg,cache,log} /tmp/* /var/tmp/*

COPY ./requirements.txt /tmp/
RUN pip3 install --upgrade pip \
 && pip3 install -r /tmp/requirements.txt \
 && rm -rf /tmp/requirements.txt

COPY stock_bot/*.py                   /opt/stock_bot/
COPY stock_bot/stock_bot.conf.default /etc/stock_bot/stock_bot.conf

VOLUME /etc/stock_bot

ENTRYPOINT ["/sbin/setuser", "nobody", "/opt/stock_bot/stock_bot.py"]
