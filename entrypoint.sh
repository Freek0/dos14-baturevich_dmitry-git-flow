#!/bin/sh
set -e
certs_dir="/etc/letsencrypt/live/bdi.bank.smodata.net"
domains="bdi.bank.smodata.net"

while true
	do
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
    certbot certonly --webroot --webroot-path /var/www/certbot/ --preferred-challenges http --http-01-port 80 --non-interactive --email baturevichdmitry@gmail.com --agree-tos -d $domains
fi
sleep 12h
done
exec "$@"
