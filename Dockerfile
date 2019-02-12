FROM python:3.7

LABEL maintainer="amit.ramon@gmail.com"

# main app dir
RUN mkdir /deps_server_app

# copy application files
COPY deps_server /deps_server_app/deps_server

# pip requirements file
COPY requirements.txt /deps_server_app

# bootstrap script
COPY bin/run_app.sh /deps_server_app

# install python packages
RUN pip install -r /deps_server_app/requirements.txt

# allow mapping this port to host
EXPOSE 8080

WORKDIR /deps_server_app

ENTRYPOINT ./run_app.sh




