FROM node:9.2-alpine as node_build

RUN mkdir /code
WORKDIR /code
ADD package.json /code/
RUN npm install .


FROM python:3.6.3-alpine

ADD . /code/
COPY --from=node_build /code/node_modules /code/node_modules

WORKDIR /code
RUN python setup.py install
