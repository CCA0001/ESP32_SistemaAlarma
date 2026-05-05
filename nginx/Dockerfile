FROM nginx:alpine
 
# Configuración del reverse proxy
COPY conf.d/default.conf /etc/nginx/conf.d/default.conf
 
# Archivos estáticos del LuxPanel
COPY html/ /usr/share/nginx/html/
 