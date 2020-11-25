FROM python:slim
ENV PYTHONBUFFERED=1
ENV	PYTHONDONTWRITEBYTECODE=1
RUN apt-get update && apt-get upgrade -y && \
	apt-get install -y libpq-dev gcc mailutils postfix && apt-get clean && \
	postconf mydestination=localhost inet_interfaces=loopback-only
WORKDIR /opt/app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY quicksell .
