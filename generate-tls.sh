#!/bin/bash
set -e

DOMAIN="wisecow.local"
CERT_DIR="./k8s/tls"
mkdir -p "$CERT_DIR"

echo ">>> Generating self-signed TLS certificate for $DOMAIN..."

openssl req -x509 -nodes -days 365 \
  -newkey rsa:2048 \
  -keyout "$CERT_DIR/tls.key" \
  -out "$CERT_DIR/tls.crt" \
  -subj "/CN=${DOMAIN}/O=wisecow" \
  -addext "subjectAltName=DNS:${DOMAIN}"

echo ">>> Creating Kubernetes TLS secret..."
kubectl create secret tls wisecow-tls \
  --cert="$CERT_DIR/tls.crt" \
  --key="$CERT_DIR/tls.key" \
  --namespace=default \
  --dry-run=client -o yaml | kubectl apply -f -

echo ">>> Done! TLS secret 'wisecow-tls' applied."
