#### Instalar pyenv

#### Configurar server

**Preparar el Sistema**: Actualiza los paquetes e instala Nginx, Python y otras dependencias básicas.

```bash
sudo apt update
sudo apt upgrade -y
sudo apt install python3-venv python3-dev libpq-dev nginx curl -y
```

**Crear un Servicio para Gunicorn**: Asegúrate de que Gunicorn se ejecute siempre en segundo plano. Crea el archivo `/etc/systemd/system/gunicorn.service` con el siguiente contenido:

```ini
[Unit]
Description=gunicorn daemon for Django
After=network.target

[Service]
User=ubuntu
Group=www-data
WorkingDirectory=/home/ubuntu/python/product_api/gymbiz-store-product-watch

ExecStartPre=/bin/mkdir -p /run/gunicorn
ExecStartPre=/bin/chown -R ubuntu:www-data /run/gunicorn
ExecStartPre=/bin/chmod -R 775 /run/gunicorn

ExecStart=/home/ubuntu/python/product_api/venv/bin/gunicorn \
          --workers 3 \
          --bind unix:/run/gunicorn/gunicorn.sock \
          --user ubuntu \
          --group www-data \
          api.wsgi

[Install]
WantedBy=multi-user.target
```

Luego, habilita e inicia el servicio:

```bash
sudo mkdir -p /run/gunicorn
sudo chown ubuntu:www-data /run/gunicorn
sudo chmod 775 /run/gunicorn

sudo systemctl start gunicorn
sudo systemctl enable gunicorn
```

**Configurar Nginx como Proxy Inverso**: Nginx recibe las peticiones web y las pasa a Gunicorn. Crea un archivo de configuración (por ejemplo, `/etc/nginx/sites-available/mi_proyecto`)

```nginx
server {
    listen 80;
    server_name localhost;

    location = /favicon.ico { access_log off; log_not_found off; }

    location /static/ {
        alias /home/ubuntu/python/product_api/gymbiz-store-product-watch/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    location / {
        include proxy_params;
        proxy_pass http://unix:/run/gunicorn/gunicorn.sock;
    }
}
```

Dar permisos en carpeta static a www-data:

```bash
sudo chown -R www-data:www-data /home/ubuntu/python/product_api/gymbiz-store-product-watch/static/
sudo chmod -R 755 /home/ubuntu/python/product_api/gymbiz-store-product-watch/static/
sudo chmod +x /home /home/ubuntu/ /home/ubuntu/python/ /home/ubuntu/python/product_api/ /home/ubuntu/python/product_api/gymbiz-store-product-watch/
```

Luego:

```bash
sudo systemctl daemon-reload
sudo systemctl restart gunicorn
sudo systemctl restart nginx
```
