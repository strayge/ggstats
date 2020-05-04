#!/bin/sh

SSL_KEY="le-key.pem"
SSL_CERT="le-crt.pem"
SSL_CHAIN_CERT="le-chain-crt.pem"

DIR="/etc/nginx/ssl/"

if [ -f "$DIR$SSL_KEY" ]; then
    exit 0
fi

openssl req \
        -x509 \
        -nodes \
        -days 365 \
        -newkey rsa:2048 \
        -subj "/C=US/ST=Test/L=Test/O=Dis/CN=localhost" \
        -keyout "$DIR$SSL_KEY" \
        -out "$DIR$SSL_CERT"

cp "$DIR$SSL_CERT" "$DIR$SSL_CHAIN_CERT"
