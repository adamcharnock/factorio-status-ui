FROM node:9.2-alpine as node_build

RUN mkdir /code
WORKDIR /code
ADD package.json /code/
RUN npm install .


FROM python:3.6.3-alpine

WORKDIR /code

COPY --from=node_build /code/node_modules /code/node_modules

ADD setup.py VERSION /code/
RUN python setup.py install

ADD factorio_status_ui /code/factorio_status_ui
RUN python setup.py develop

ADD static /code/static
ADD templates /code/templates

VOLUME /mods
VOLUME /saves

ENTRYPOINT ["factorio_status_ui"]
CMD []
