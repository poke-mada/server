FROM nginx:1.17.4

RUN mkdir /static/
RUN mkdir /certificates/
RUN rm /etc/nginx/conf.d/default.conf
COPY ./compose/nginx/nginx.conf /etc/nginx/conf.d/