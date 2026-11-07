FROM nginx:alpine
COPY default.conf /etc/nginx/conf.d/default.conf
COPY e2e.htpasswd /etc/nginx/e2e.htpasswd
COPY content/ /usr/share/nginx/html/
EXPOSE 80
