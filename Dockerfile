FROM alpine:latest

RUN apk add --no-cache \
      build-base \
      linux-headers \
      postgresql-client \
      postgresql-dev \
      python3 \
      python3-dev

RUN pip3 install --no-cache-dir --disable-pip-version-check psycopg2 sqlalchemy

RUN adduser -D student

USER student
WORKDIR /data
ENTRYPOINT ["/bin/sh"]
