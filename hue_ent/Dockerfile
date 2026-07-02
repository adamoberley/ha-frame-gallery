# Hue Entertainment bridge for Home Assistant.
#
# Pin the Debian base directly (same reasoning as the ledfx app: the Supervisor
# doesn't always honor build.yaml's build_from, and python:3.12-slim is
# multi-arch). The app is pure Python with one small dependency - no toolchain.
FROM python:3.12-slim

ENV LANG=C.UTF-8 \
    PYTHONUNBUFFERED=1

COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt && rm /tmp/requirements.txt

COPY app /opt/hue_ent/app
COPY run.sh /run.sh
RUN chmod a+x /run.sh

WORKDIR /opt/hue_ent
CMD [ "/run.sh" ]
