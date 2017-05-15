# Default server host
#
# VERSION               0.1
#

FROM     hypriot/rpi-alpine-scratch
MAINTAINER Andrey Derevyagin "2derand@gmail.com"

ADD history.py requirements.txt create_frames.py data-latin.ttf /app/

RUN apk -U upgrade && apk -U add tzdata ca-certificates python python-dev py-pip gcc linux-headers musl-dev freetype-dev zlib-dev jpeg-dev libpng-dev libffi-dev openssl-dev && update-ca-certificates && \
    cp /usr/share/zoneinfo/Europe/Kiev /etc/localtime && \
    pip install -r /app/requirements.txt && \
    chmod a+x /app/history.py /app/create_frames.py && \
    apk del py-pip gcc linux-headers musl-dev && \
    rm -rf /var/cache/apk/*

ENTRYPOINT ["/app/history.py"]
