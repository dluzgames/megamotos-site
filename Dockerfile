FROM nginx:alpine

# Remove página padrão do nginx
RUN rm -rf /usr/share/nginx/html/*

# Copia os arquivos do site para o diretório de publicação do Nginx
COPY . /usr/share/nginx/html

# Configuração otimizada para SEO, compressão Gzip, 404 real e controle de cache
RUN cat <<'EOF' > /etc/nginx/conf.d/default.conf
server {
    listen 80;
    server_name localhost;
    root /usr/share/nginx/html;
    index index.html index.htm;

    gzip on;
    gzip_vary on;
    gzip_min_length 256;
    gzip_types text/plain text/css application/javascript application/json image/svg+xml application/xml text/xml application/manifest+json;

    location ~* \.(?:html?|xml|txt|webmanifest)$ {
        add_header Cache-Control "no-cache, must-revalidate";
        try_files $uri $uri/ =404;
    }

    location ~* \.(?:css|js|jpg|jpeg|png|gif|ico|svg|webp|woff2?)$ {
        add_header Cache-Control "public, max-age=604800";
        try_files $uri =404;
    }

    location / {
        add_header Cache-Control "no-cache, must-revalidate";
        try_files $uri $uri/ =404;
    }

    error_page 500 502 503 504 /50x.html;
    location = /50x.html {
        root /usr/share/nginx/html;
    }
}
EOF

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
