FROM python:slim
ENV PYTHONBUFFERED=1
RUN apt-get update && apt-get upgrade -y
WORKDIR /opt/app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY quicksell ./quicksell
