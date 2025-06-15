#!/bin/sh
set -eu

CERT_DIR="${CERT_DIR:-/certs}"
mkdir -p "$CERT_DIR"

CA_KEY="$CERT_DIR/ca.key"
CA_CERT="$CERT_DIR/ca.crt"
SERVER_KEY="$CERT_DIR/server.key"
SERVER_CSR="$CERT_DIR/server.csr"
SERVER_CERT="$CERT_DIR/server.crt"

# Generate CA if missing
if [ ! -f "$CA_KEY" ] || [ ! -f "$CA_CERT" ]; then
    echo "[*] Generating new CA certificate"
    openssl req -x509 -nodes -new -newkey rsa:2048 -days 365 \
        -subj "/CN=mcp-ca" \
        -keyout "$CA_KEY" -out "$CA_CERT"
fi

# Always (re)generate server certificate for now; rotate every start
echo "[*] Generating server certificate signed by CA"
openssl req -new -nodes -newkey rsa:2048 \
    -subj "/CN=mcp-server" \
    -keyout "$SERVER_KEY" -out "$SERVER_CSR"

openssl x509 -req -in "$SERVER_CSR" -CA "$CA_CERT" -CAkey "$CA_KEY" \
    -CAcreateserial -out "$SERVER_CERT" -days 90

rm -f "$SERVER_CSR" "$CERT_DIR/ca.srl" 2>/dev/null || true

ls -l "$CERT_DIR"

echo "[*] Certificate generation complete. Sleeping to keep sidecar alive."
exec sleep infinity 