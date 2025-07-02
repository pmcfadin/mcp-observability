#!/bin/sh
set -eu

# Default uvicorn app path
APP_MODULE=${APP_MODULE:-app.main:app}
HOST=${HOST:-0.0.0.0}
PORT=${PORT:-8000}

CMD="uvicorn ${APP_MODULE} --host ${HOST} --port ${PORT}"

# Enable TLS when either TLS_ENABLED=1 or SSL_CERTFILE path provided
if [ "${TLS_ENABLED:-}" = "1" ] || [ -n "${SSL_CERTFILE:-}" ]; then
  CERT=${SSL_CERTFILE:-/certs/server.crt}
  KEY=${SSL_KEYFILE:-/certs/server.key}
  CMD="$CMD --ssl-certfile ${CERT} --ssl-keyfile ${KEY}"
  if [ -n "${SSL_CA_CERT:-}" ]; then
    CMD="$CMD --ssl-ca-certs ${SSL_CA_CERT}"
  fi
fi

exec sh -c "${CMD}"
