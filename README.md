# filehoster
Make your file accessible to everyone with just one link

![Dashboard](https://file.techniqstone.net/files/96XDaoUa8x3a)

### Quickstart install
```bash
git clone https://github.com/WrobelXXL/filehoster.git && cd filehoster && chmod +x setup.sh && ./setup.sh
```

### filehoster Docker stoppen
```bash
docker compose down
```

### filehoster Docker starten
```bash
docker compose up -d --build
```

### Apache file.conf `/etc/apache2/sites-available/file.conf`
```
<VirtualHost *:443>
    ServerName file.techniqstone.net

    SSLEngine on
    SSLCertificateFile /etc/ssl/certs/file.pem
    SSLCertificateKeyFile /etc/ssl/private/file.key

    ProxyPreserveHost On
    ProxyPass / http://0.0.0.0:8110/
    ProxyPassReverse / http://0.0.0.0:8110/

    ErrorLog ${APACHE_LOG_DIR}/file_error.log
    CustomLog ${APACHE_LOG_DIR}/file_access.log combined
</VirtualHost>
```
> Apache conf aktivieren `sudo a2ensite file.conf`
