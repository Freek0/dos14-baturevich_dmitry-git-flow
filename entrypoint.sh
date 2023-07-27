#!/bin/sh
set -e
certs_dir="/etc/letsencrypt/live/bdi.bank.smodata.net"
domains="bdi.bank.smodata.net"

if [ -d "$certs_dir" ]; then
    echo "Сертификаты уже существуют"
    if certbot certificates --domain $domains --quiet; then
        echo "Сертификаты актуальны"
    else
        echo "Сертификаты устарели"
        certbot renew --quiet
    fi
else
    echo "Сертификаты отсутствуют"
    certbot certonly --standalone --preferred-challenges http --http-01-port 80 --non-interactive --email baturevichdmitry@gmail.com --agree-tos --no-eff-email --staging -d $domains
fi
exec "$@"